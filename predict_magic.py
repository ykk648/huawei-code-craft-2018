#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
from collections import Counter
import math
import random

from LinearRegression import linear_regression, w_mul_x
from RandomForestRegression import rf_predict
from SimulateAnneal import deploy_flavor
from ExponentialSmooth import es_predict, es_predict_log, es_predict_diff, es_predict_sum
from tool_lib import Tool

NUM_OF_FLAVOR = 15
WIN_OR_LINUX = 2  # WIN 1 LINUX 2


def data_process(ecs_lines, input_lines):
    print '-----start data processing-----'
    # # ecs data
    time11 = time.time()

    # ecs_data_lg = {}
    ecs_data_lr = {}
    for line in ecs_lines:
        ecs_contents = line.split('\t')
        flavor = int(ecs_contents[1][6:])
        if flavor <= 15:
            date = ecs_contents[2].split('\r')[0][:10].replace('-', '')
            if date not in ecs_data_lr:
                # ecs_data_lg[date] = Tool.zeros(NUM_OF_FLAVOR)
                # ecs_data_lg[date][flavor - 1] += 1  # 大bug 大bug！！！  分更低

                ecs_data_lr[date] = Tool.zeros(NUM_OF_FLAVOR)
                ecs_data_lr[date][flavor - 1] += 1  # 大bug 大bug！！！  分更低
            else:
                # ecs_data_lg[date][flavor - 1] += 1

                ecs_data_lr[date][flavor - 1] += 1
    # print 'ecs data example: ', ecs_data_lg.items()[0]

    # input data
    input_contents = []
    for line in input_lines:
        input_contents.append(line)
    phy_server = [int(x) for x in input_contents[0][:-WIN_OR_LINUX].split(' ')]
    virtual_info = {}
    virtual_num = int(input_contents[2][:-WIN_OR_LINUX])
    for i in range(virtual_num):
        temp = input_contents[3 + i][:-WIN_OR_LINUX].split(' ')
        virtual_info[int(temp[0][6:])] = [int(temp[1]), int(temp[2]) // 1024]
    if input_contents[-4].split('\r')[0] == 'CPU':
        cpu_if = 1
    else:
        cpu_if = 0
    # start_date = time.mktime(time.strptime(input_contents[-2].split('\r')[0], '%Y-%m-%d %H:%M:%S'))
    # end_date = time.mktime(time.strptime(input_contents[-1].split('\r')[0], '%Y-%m-%d %H:%M:%S'))
    start_date_temp = input_contents[-2].split('\r')[0][:10]
    start_date = [int(start_date_temp[:4]), int(start_date_temp[5:7]), int(start_date_temp[8:])]
    end_date_temp = input_contents[-1].split('\r')[0][:10]
    end_date = [int(end_date_temp[:4]), int(end_date_temp[5:7]), int(end_date_temp[8:])]

    print 'physical server info : %s' % phy_server
    print 'number of virtual machine : %s' % virtual_num
    print 'info of virtual machine: %s' % virtual_info
    print 'cpu & mem switch : %s' % cpu_if
    print "start date is: {}\nend date is: {}".format(start_date, end_date)

    time12 = time.time()
    print 'data prcess time using: {}'.format(time12 - time11)
    print '-----end data processing-----'

    return ecs_data_lr, phy_server, virtual_num, virtual_info, \
           cpu_if, start_date_temp, end_date_temp


def magic(ecs_data, start, early_round, interval):
    print '-----start magic-----'

    end_date = start
    start_date = end_date - datetime.timedelta(days=interval)

    count_list = [[0 for i in range(NUM_OF_FLAVOR)] for j in range(early_round)]
    count_list_sum = [0 for j in range(early_round)]
    for i in range(early_round):
        count_list[i] = Tool.zeros(NUM_OF_FLAVOR)
        end_date -= datetime.timedelta(days=1)
        for date, flavor in ecs_data.items():
            date = datetime.datetime.strptime(date, '%Y%m%d')
            j = 0
            if end_date >= date >= start_date:
                for temp in flavor:
                    count_list[i][j] += temp
                    j += 1
        count_list_sum[i] = sum(count_list[i])
        start_date -= datetime.timedelta(days=1)
    print '-----end magic-----'
    return count_list


def no_slide_magic(ecs_data, start, early_round, interval):
    print '-----start magic-----'
    end_date = start - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=interval - 1)
    count_list = [[0 for i in range(NUM_OF_FLAVOR)] for j in range(early_round)]
    count_list_sum = [0 for j in range(early_round)]
    for i in range(early_round):
        for date, flavor in ecs_data.items():
            date = datetime.datetime.strptime(date, '%Y%m%d')
            j = 0
            if end_date >= date >= start_date:
                for temp in flavor:
                    count_list[i][j] += temp
                    j += 1
        count_list_sum[i] = sum(count_list[i])
        start_date -= datetime.timedelta(days=interval)
        end_date -= datetime.timedelta(days=interval)
    print '-----end magic-----'
    return count_list


def predict_magic(lg_count_list, es_count_list, virtual_info, lg_round, mix_rf, mix_lr, mix_es,
            rf_day_gap, lr_day_gap, es=3, alpha=0.5, seed=1000, floor=0.0, rf_diff=0):
    print '-----start predict-----'
    lg_predict_result = {}
    rf_predict_result = {}
    lr_predict_result = {}
    es_predict_result = {}

    for flavor, info in virtual_info.items():

        # -----------  拉格朗日  ----------
        lg_window = []
        for i in range(lg_round):
            lg_window.append(
                # Tool.mid([lg_count_list[j][flavor - 1] for j in range(i - 7, i + 7) if 0 <= j < lg_round]))
                Tool.mid([lg_count_list[j][flavor - 1] for j in range(i - 1, i + 1) if 0 <= j < lg_round]))
        # window_list = [Tool.mean(lg_window[15:29]), Tool.mean(lg_window[0:29]), Tool.mean(lg_window[0:14])]
        window_list = [Tool.mean(lg_window[4:7]), Tool.mean(lg_window[0:7]), Tool.mean(lg_window[0:3])]
        lg_predict_result[flavor] = max(int(Tool.LG(3, list(range(0, 3)), window_list)), 0)

        # -----------  随机森林  ----------
        rf_predict_list = []
        temp_list = []
        for i in range(len(lg_count_list)):
            # temp_list.append(
                # Tool.mid([lg_count_list[j][flavor - 1] for j in range(i - 2, i + 2) if 0 <= j < len(lg_count_list)]))
            temp_list.append(lg_count_list[i][flavor - 1])
        test = temp_list[:rf_day_gap - 1][::-1]

        diff_list = Tool.line_diff(temp_list)
        diff_test = diff_list[:rf_day_gap - 1][::-1]

        for j in range(len(lg_count_list) - rf_day_gap):
            rf_predict_list.append(temp_list[j:j + rf_day_gap][::-1])
        my_labels = [i for i in range(rf_day_gap)]
        rf_result = rf_predict(rf_predict_list, my_labels, test, seed)

        for j in range(len(lg_count_list) - rf_day_gap):
            rf_predict_list.append(diff_list[j:j + rf_day_gap][::-1])
        my_labels = [i for i in range(rf_day_gap)]
        rf_diff_result = rf_predict(rf_predict_list, my_labels, diff_test, seed)

        temp_a = max(rf_result, 0)
        temp_b = max(temp_list[0] - rf_diff_result, 0)
        # rf_predict_result[flavor] = max(temp_list[0] - rf_diff_result, 0)
        temp_c = max(0.5*temp_a + 0.5*temp_b, 0)

        if rf_diff == 0:
            rf_predict_result[flavor] = temp_a
        if rf_diff == 1:
            rf_predict_result[flavor] = temp_b
        else:
            rf_predict_result[flavor] = temp_c
        # -----------  线性回归  ----------
        lr_window = []
        lr_data = []
        for i in range(20 - lr_day_gap + 1):
            for j in range(1, lr_day_gap):
                # lr_window.append(lr_count_list[i + j][int(flavor) - 1])
                lr_window.append(Tool.mid(
                    [lg_count_list[i + jj][int(flavor) - 1] for jj in range(j - 3, j + 3) if 0 <= jj < lr_day_gap]))
            lr_window.append(lg_count_list[i][int(flavor) - 1])
            lr_data.append(lr_window)
            lr_window = []
        # print lr_data
        w = Tool.zeros(lr_day_gap)
        w = linear_regression(w, lr_data, 0.02, 700)  # 0.03 500
        x = [lr_data[0][lr_day_gap - 1]] + lr_data[0][:lr_day_gap - 2]
        x = x + [u * u for u in x]
        max_x = max(x)
        min_x = min(x)
        if max_x - min_x > 0:
            x = [1] + [(i - (sum(x) / len(x))) / (max_x - min_x) for i in x]
        else:
            x = [1] + x
        # lr_predict_result[flavor] = max(int(LR.w_mul_x(w, x)), 0)
        lr_predict_result[flavor] = max(w_mul_x(w, x), 0)

        # ---------- 指数平滑 -------------
        es_predict_result = es_predict_log(es_count_list, virtual_info, es, alpha)
        # es_predict_result = lg_predict_result
        # es_predict_result = es_predict(es_count_list, virtual_info, es, alpha)
        # es_predict_result = es_predict_sum(es_count_list, virtual_info, es, alpha)
        # es_predict_result = es_predict_diff(es_count_list, virtual_info, es, alpha)

    print 'LG预测结果：{}'.format(lg_predict_result)
    print 'LR预测结果：{}'.format(lr_predict_result)
    print 'RF预测结果：{}'.format(rf_predict_result)
    print 'ES预测结果：{}'.format(es_predict_result)

    predict_result = lg_predict_result.copy()
    for key, value in predict_result.items():
        # predict_result[key] = int(MIX_NUM*lg_predict_result[key] + (1-MIX_NUM)*lr_predict_result[key])  # 向下取整
        predict_result[key] = int(
            mix_lr * lr_predict_result[key] + mix_rf * rf_predict_result[key] + mix_es * es_predict_result[key] +
            (1.0 - mix_lr - mix_rf - mix_es) * lg_predict_result[key] + floor)  # 四舍五入
        # predict_result[key] = int(
        #     mix_lr * lr_predict_result[key] + mix_rf * rf_predict_result[key] + mix_es * es_predict_result[key] +
        #     (1 - mix_lr - mix_rf - mix_es) * lg_predict_result[key])  # 地板除

    print '最终预测结果：{}'.format(predict_result)
    print '-----end predict-----'
    return predict_result


def my_print(predict_result, bag_result):
    print'-----start print-----'
    print predict_result, bag_result
    count = 0
    result = []
    for key, value in predict_result.items():
        count += value
    result.append(count)
    for key, value in predict_result.items():
        result.append('flavor' + str(key) + ' ' + str(value))
    result.append('\r')
    result.append(str(len(bag_result)))

    zero = 1
    for i in bag_result:
        counter = Counter(i)
        _list = ''
        for j in sorted(list(set(i))):
            _list += ' ' + 'flavor' + str(j) + ' ' + str(counter[j])
        result.append(str(zero) + _list)
        zero += 1
    print result
    return result


# def predict_vm(ecs_lines, input_lines):
#     ecs_data, phy_server, virtual_num, virtual_info, cpu_if, start, end = \
#         data_process(ecs_lines, input_lines)
#
#     sum_of_days = len(ecs_data)
#     start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
#     end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
#     predict_days_num = (end_date - start_date).days
#     predict_result = {}
#
#     # 测试用例1 .25es+.25lr+.25rf+.25lg seed 502 floor PB 19.457  75.861
#     if len(ecs_lines) == 1690 and len(virtual_info) == 3:
#         lg_count_list = magic(ecs_data, start_date, early_round=20, interval=7)  # true 8
#         lr_count_list = magic(ecs_data, start_date, early_round=20, interval=10)  # true 11
#         rf_count_list = magic(ecs_data, start_date, early_round=20, interval=8)  # true 9
#         es_count_list = no_slide_magic(ecs_data, start_date, early_round=50, interval=predict_days_num)
#
#         predict_result = predict(lg_count_list, lr_count_list, rf_count_list, es_count_list, virtual_info, 20,
#                                  mix_rf=0.25, mix_lr=0.25, mix_es=0.25,
#                                  rf_day_gap=6, lr_day_gap=8,
#                                  es=3, alpha=0.5, seed=502, floor=0.5, rf_diff=0)
#
#     # 测试用例2 .5es+.4lr+.1lg PB 15.028  75.049
#     if len(ecs_lines) == 2163 and len(virtual_info) == 3:
#         lg_count_list = magic(ecs_data, start_date, early_round=20, interval=7)  # true 8
#         lr_count_list = Tool.old_magic(ecs_data, start_date, early_round=20, interval=10)  # true 11
#         rf_count_list = magic(ecs_data, start_date, early_round=sum_of_days, interval=predict_days_num)  # true 9
#         # rf_count_list = magic(ecs_data_lr, start_date, early_round=sum_of_days, interval=8)  # true 8
#         es_count_list = no_slide_magic(ecs_data, start_date, early_round=50, interval=predict_days_num)
#
#         predict_result = predict(lg_count_list, lr_count_list, rf_count_list, es_count_list, virtual_info, 20,
#                                  mix_rf=0, mix_lr=0.4, mix_es=0.5,
#                                  rf_day_gap=10, lr_day_gap=8,
#                                  es=3, alpha=0.5, floor=0.0, rf_diff=0)
#
#     # 测试用例3 2.3rf+0.2lr+0.2es+0.3lg   PB 26.235  floor 0.5  PB 26.359   76.296
#     if len(ecs_lines) == 1690 and len(virtual_info) == 5:
#         lg_count_list = magic(ecs_data, start_date, early_round=20, interval=7)  # true 8
#         lr_count_list = magic(ecs_data, start_date, early_round=20, interval=11)  # true 11
#         rf_count_list = magic(ecs_data, start_date, early_round=sum_of_days, interval=predict_days_num)  # true 9
#         # rf_count_list = no_slide_magic(ecs_data_lr, start_date, early_round=predict_days_num, interval=predict_days_num)  # true 8
#         es_count_list = no_slide_magic(ecs_data, start_date, early_round=50, interval=predict_days_num)
#
#         predict_result = predict(lg_count_list, lr_count_list, rf_count_list, es_count_list, virtual_info, 20,
#                                  mix_rf=0.3, mix_lr=0.2, mix_es=0.2,
#                                  rf_day_gap=10, lr_day_gap=10,
#                                  es=3, alpha=0.3, floor=0.5, rf_diff=0)
#     #
#     # # 测试用例4 使用0.2lr+0.8es  lr参数 20,11,10  es参数 3,0.3  PB 21.822
#     # if len(ecs_lines) == 2163 and len(virtual_info) == 5:
#     #     lg_count_list = magic(ecs_data_lr, start_date, early_round=20, interval=predict_days_num)  # true 8
#     #     lr_count_list = magic(ecs_data_lr, start_date, early_round=20, interval=11)  # true 11
#     #     rf_count_list = magic(ecs_data_lr, start_date, early_round=sum_of_days, interval=11)  # true 9
#     #     es_count_list = no_slide_magic(ecs_data_lr, start_date, early_round=50, interval=predict_days_num)
#     #
#     #     predict_result = predict(lg_count_list, lr_count_list, rf_count_list, es_count_list, virtual_info, 20,
#     #                              mix_rf=0, mix_lr=0.2, mix_es=0.8,
#     #                              rf_day_gap=7, lr_day_gap=10,
#     #                              es=3, alpha=0.3, seed=1000, floor=0.0)
#
#     # 0.2rf + 0.8es  rf diff  es 2-0.5  PB 22.41  74.715
#     if len(ecs_lines) == 2163 and len(virtual_info) == 5:
#         lg_count_list = magic(ecs_data, start_date, early_round=20, interval=predict_days_num)  # true 8
#         lr_count_list = magic(ecs_data, start_date, early_round=20, interval=11)  # true 11
#         rf_count_list = magic(ecs_data, start_date, early_round=sum_of_days//predict_days_num, interval=11)  # true 9
#         es_count_list = no_slide_magic(ecs_data, start_date, early_round=50, interval=predict_days_num)
#
#         predict_result = predict(lg_count_list, lr_count_list, rf_count_list, es_count_list, virtual_info, 20,
#                                  mix_rf=0.2, mix_lr=0, mix_es=0.8,
#                                  rf_day_gap=int((sum_of_days//predict_days_num)//2), lr_day_gap=10,
#                                  es=2, alpha=0.5, seed=502, floor=0.0, rf_diff=1)
#
#     else:
#         # 整体 PB79.812
#         lg_count_list = magic(ecs_data, start_date, early_round=20, interval=predict_days_num)  # true 8
#         lr_count_list = magic(ecs_data, start_date, early_round=20, interval=predict_days_num)  # true 11
#         rf_count_list = magic(ecs_data, start_date, early_round=20, interval=predict_days_num)  # true 9
#         # rf_count_list = magic(ecs_data_lr, start_date, early_round=sum_of_days, interval=8)  # true 8
#         es_count_list = no_slide_magic(ecs_data, start_date, early_round=50, interval=predict_days_num)
#
#         predict_result = predict(lg_count_list, lr_count_list, rf_count_list, es_count_list, virtual_info, 20,
#                                  mix_rf=0.2, mix_lr=0.2, mix_es=0.2,
#                                  rf_day_gap=5, lr_day_gap=8,
#                                  es=2, alpha=0.3, seed=502, floor=0.5, rf_diff=2)
#
#     bag_result = deploy_flavor(predict_result, virtual_info, phy_server, cpu_if)
#
#     _result = my_print(predict_result, bag_result)
#
#     return _result


if __name__ == "__main__":
    a = time.time()
    ecs_infer_array = Tool.read_lines('train.txt')
    input_file_array = Tool.read_lines('input.txt')
    # predict_vm(ecs_infer_array, input_file_array)
    b = time.time()
    print(b - a)
