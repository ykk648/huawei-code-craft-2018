#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import datetime

class Tool():
    @classmethod
    def mean(cls, array):
        return float(sum(array)) / len(array)

    @classmethod
    def mid(cls, array):
        return sorted(array)[len(array) // 2]

    @classmethod
    def zeros(cls, num):
        return [0] * num

    @classmethod
    def LG(cls, z, x, y):
        ans = 0.0
        for i in range(len(x)):
            t = 1.0
            for j in range(len(x)):
                if i != j:
                    t = t * (z - x[j]) / (x[i] - x[j])
            ans = ans + t * y[i]
        return ans

    @classmethod
    def read_lines(cls, file_path):
        if os.path.exists(file_path):
            array = []
            with open(file_path, 'r') as lines:
                for line in lines:
                    array.append(line)
            return array
        else:
            print 'file not exist: ' + file_path
            return None

    @classmethod
    def predict_process(cls, predict_result, virtual_info):
        count = 0
        _predict = []
        for flavor, num in predict_result.items():
            count += num
            for i in range(num):
                _predict.append([int(flavor), int(virtual_info[flavor][0]), int(virtual_info[flavor][1])])
        return count, _predict

    @classmethod
    def old_magic(cls,ecs_data, start, early_round, interval):
        print '-----start magic-----'

        end_date = start
        start_date = end_date - datetime.timedelta(days=interval)

        count_list = [[0 for i in range(15)] for j in range(early_round)]
        count_list_sum = [0 for j in range(early_round)]
        for i in range(early_round):
            count_list[i] = Tool.zeros(15)
            end_date -= datetime.timedelta(days=1)
            start_date -= datetime.timedelta(days=1)
            for date, flavor in ecs_data.items():
                date = datetime.datetime.strptime(date, '%Y%m%d')
                j = 0
                if end_date >= date >= start_date:
                    for temp in flavor:
                        count_list[i][j] += temp
                        j += 1
            count_list_sum[i] = sum(count_list[i])

        print '-----end magic-----'
        return count_list

    # @classmethod
    # def diff(cls, count_list, interval=1):
    #     result = [[] for j in range(0, len(count_list)-1)]
    #     temp = []
    #     first_value = count_list[-1]
    #     for i in range(len(count_list[0])):
    #         # first_value.append(count_list[-1])
    #         temp = []
    #         for j in range(interval, len(count_list)):
    #             value = count_list[::-1][j][i] - count_list[::-1][j - interval][i]
    #             temp.append(value)
    #             result[j-1].append(value)
    #     result = result[::-1]
    #     return result, first_value

    @classmethod
    def line_diff(cls, count_list, interval = 1):
        result = []
        for i in range(interval, len(count_list)):
            value = count_list[i] - count_list[i - interval]
            result.append(value)
        return result

    # @classmethod
    # def rediff(cls, result, first_value, interval=1):
    #     count_list = []
    #     for i in range(len(result[0])):
    #         temp = []
    #         # temp.append(first_value)
    #         # temp.append(first_value)
    #         value = first_value[i]
    #         for j in range(len(result)):
    #             value += result[j][i]
    #             temp.append(value)
    #         count_list.append(temp)
    #     return count_list



    @classmethod
    def deployVM(cls, factor, count_all, predict_temp, phy_server):
        if factor == 1:  # CPU
            server = int(phy_server[1])  # MEM
            limit = int(phy_server[0])
            capacity = 2
            weight = 1
        else:
            server = int(phy_server[0])
            limit = int(phy_server[1])
            capacity = 1
            weight = 2
        bag_temp = [[0 for col in range(server + 1)] for raw in range(count_all + 1)]
        result = []

        for i in range(1, count_all + 1):
            for j in range(1, server + 1):
                bag_temp[i][j] = bag_temp[i - 1][j]
                if j >= predict_temp[i - 1][capacity]:
                    bag_temp[i][j] = max(bag_temp[i][j],
                                         bag_temp[i - 1][j - predict_temp[i - 1][capacity]] + predict_temp[i - 1][
                                             weight])
                if bag_temp[i][j] > limit:
                    n = j - 1
                    for m in range(i, 0, -1):
                        if bag_temp[m][n] > bag_temp[m - 1][n]:
                            result.append(predict_temp[m - 1][0])
                            n = n - predict_temp[m - 1][capacity]
                    return result
        j = server

        for i in range(count_all, 0, -1):
            if bag_temp[i][j] > bag_temp[i - 1][j]:
                result.append(predict_temp[i - 1][0])
                j = j - predict_temp[i - 1][capacity]
        return result
    #
    #
    # # old 多重背包装箱方法
    @classmethod
    def bag(cls, predict_result, cpu, virtual_info, phy_server):
        print '-----start bagging-----'
        result_temp = predict_result.copy()
        bag_result = []
        count, _predict = Tool.predict_process(result_temp, virtual_info)

        while count >= 1:
            bag_result_temp = Tool.deployVM(cpu, count, _predict, phy_server)
            for i in bag_result_temp:
                result_temp[i] -= 1
            count, _predict = Tool.predict_process(result_temp, virtual_info)
            bag_result.append(bag_result_temp)
        print bag_result
        print '-----end bagging-----'
        return bag_result
    #
    # # old 旧的装箱方法
    # @classmethod
    # def box(cls, predict_result, cpu, virtual_info, phy_server):
    #     map_list = []
    #     target = int(-(cpu - 1))
    #     virtual_info_sort = sorted(virtual_info.items(), key=lambda item: -item[1][target])
    #     nums_remain = sum(predict_result.values())
    #     predict_copy = predict_result.copy()
    #     serve_remain = []
    #     while nums_remain > 0:
    #         serve_remain.append(phy_server[:2])
    #         map_list.append([])
    #         for id, value in virtual_info_sort:
    #             while predict_copy[id] > 0 and serve_remain[-1][0] >= value[0] and serve_remain[-1][1] >= value[1]:
    #                 map_list[-1].append(id)
    #                 predict_copy[id] -= 1
    #                 serve_remain[-1][0] -= value[0]
    #                 serve_remain[-1][1] -= value[1]
    #                 nums_remain -= 1
    #     return map_list


if __name__ == '__main__':
    # count_list = [[1, 2, 1, 0, 3, 3, 11, 28, 8, 4, 4, 1, 0, 0, 0], [2, 4, 1, 1, 4, 0, 4, 12, 6, 0, 3, 9, 1, 4, 1],
    #               [0, 2, 3, 0, 4, 8, 1, 14, 1, 0, 14, 0, 0, 4, 0], [0, 0, 1, 0, 3, 1, 0, 4, 0, 0, 3, 1, 0, 8, 0],
    #               [0, 2, 1, 1, 4, 3, 0, 7, 7, 0, 7, 5, 0, 1, 5], [0, 0, 3, 2, 14, 1, 1, 6, 3, 0, 2, 14, 0, 27, 21],
    #               [0, 1, 0, 0, 0, 2, 0, 4, 3, 0, 4, 8, 0, 0, 4], [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2],
    #               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    # result, first = Tool.diff(count_list)
    # print result
    # print first
    # count_list = Tool.rediff(result, first)
    # print count_list
    count_list = [1, 2, 1, 0, 3, 3, 11, 28, 8, 4, 4, 1, 0, 0, 0]
    a = Tool.line_diff(count_list)
    print a