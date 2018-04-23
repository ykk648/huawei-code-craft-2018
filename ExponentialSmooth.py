# -*- coding: utf-8 -*-

import math
from tool_lib import Tool


def exponential_smoothing(alpha, s):
    s_temp = [0 for i in range(len(s))]
    s_temp[0] = s[0]
    for i in range(1, len(s)):
        s_temp[i] = alpha * s[i] + (1 - alpha) * s_temp[i - 1]
    return s_temp


def compute_single(alpha, s):
    return exponential_smoothing(alpha, s)


def compute_double(alpha, s):
    s_single = compute_single(alpha, s)
    s_double = compute_single(alpha, s_single)

    a_double = [0 for i in range(len(s))]
    b_double = [0 for i in range(len(s))]

    for i in range(len(s)):
        a_double[i] = 2 * s_single[i] - s_double[i]  # 计算二次指数平滑的a
        b_double[i] = (alpha / (1 - alpha)) * (s_single[i] - s_double[i])  # 计算二次指数平滑的b

    return a_double, b_double


def compute_triple(alpha, s):
    s_single = compute_single(alpha, s)
    s_double = compute_single(alpha, s_single)
    s_triple = exponential_smoothing(alpha, s_double)

    a_triple = [0 for i in range(len(s))]
    b_triple = [0 for i in range(len(s))]
    c_triple = [0 for i in range(len(s))]

    for i in range(len(s)):
        a_triple[i] = 3 * s_single[i] - 3 * s_double[i] + s_triple[i]
        b_triple[i] = (alpha / (2 * ((1 - alpha) ** 2))) * (
                (6 - 5 * alpha) * s_single[i] - 2 * ((5 - 4 * alpha) * s_double[i]) + (4 - 3 * alpha) * s_triple[i])
        c_triple[i] = ((alpha ** 2) / (2 * ((1 - alpha) ** 2))) * (s_single[i] - 2 * s_double[i] + s_triple[i])

    return a_triple, b_triple, c_triple


def es_predict(count_list, virtual_info, double_or_triple, alpha):
    # temp_list = []
    es_predict_result = {}
    for flavor, info in virtual_info.items():
        temp_list = []
        for i in range(len(count_list)):
            temp_list.append(count_list[i][flavor - 1])
            # temp_list.append(Tool.mid([count_list[j][flavor - 1] for j in range(i - 3, i + 3) if 0 <= j < len(count_list)]))
        temp_list = temp_list[::-1]
        if double_or_triple == 2:
            a, b = compute_double(alpha, temp_list)
            es_predict_result[flavor] = max(int(a[-1] + b[-1] * 1), 0)
        elif double_or_triple == 3:
            a, b, c = compute_triple(alpha, temp_list)
            es_predict_result[flavor] = max(int(a[-1] + b[-1] * 1 + c[-1] * (1 ** 2)), 0)
    return es_predict_result


def es_predict_log(count_list, virtual_info, double_or_triple, alpha):
    # temp_list = []
    es_predict_result = {}
    for flavor, info in virtual_info.items():
        temp_list = []
        for i in range(len(count_list)):
            # temp_a = count_list[i][flavor - 1]
            temp_a = Tool.mid([count_list[j][flavor - 1] for j in range(i - 2, i + 2) if 0 <= j < len(count_list)])
            temp_list.append(
                math.log(
                    int(temp_a) + 1))
        temp_list = temp_list[::-1]
        if double_or_triple == 2:
            a, b = compute_double(alpha, temp_list)
            es_predict_result[flavor] = max(math.exp(a[-1] + b[-1] * 1) - 1, 0)
        elif double_or_triple == 3:
            a, b, c = compute_triple(alpha, temp_list)
            es_predict_result[flavor] = max(math.exp(a[-1] + b[-1] * 1 + c[-1] * (1 ** 2)) - 1, 0)
    return es_predict_result


def es_predict_diff(count_list, virtual_info, double_or_triple, alpha):
    # temp_list = []
    es_predict_result = {}
    for flavor, info in virtual_info.items():
        temp_list = []
        for i in range(len(count_list)):
            temp_list.append(count_list[i][flavor - 1])
        es_list = Tool.line_diff(temp_list[::-1])
        if double_or_triple == 2:
            a, b = compute_double(alpha, es_list)
            aaa = int(a[-1] + b[-1] * 1)
            es_predict_result[flavor] = max(temp_list[0] + aaa, 0)
        elif double_or_triple == 3:
            a, b, c = compute_triple(alpha, es_list)
            bbb = int(a[-1] + b[-1] * 1 + c[-1] * (1 ** 2))
            es_predict_result[flavor] = max(temp_list[0] + bbb, 0)
    return es_predict_result


def es_predict_sum(count_list, virtual_info, double_or_triple, alpha):
    # temp_list = []
    es_predict_result = {}
    for flavor, info in virtual_info.items():
        temp_list1 = []
        temp_list2 = []
        temp_list3 = []
        for i in range(len(count_list)):
            temp_list1.append(count_list[i][flavor - 1])

            temp_a = Tool.mid([count_list[j][flavor - 1] for j in range(i - 2, i + 2) if 0 <= j < len(count_list)])
            temp_list2.append(
                math.log(
                    int(temp_a) + 1))

            temp_list3.append(count_list[i][flavor - 1])

        temp_list1 = temp_list1[::-1]
        temp_list2 = temp_list2[::-1]
        es_list3 = Tool.line_diff(temp_list3[::-1])

        if double_or_triple == 2:
            a1, b1 = compute_double(alpha, temp_list1)
            result1 = max(int(a1[-1] + b1[-1] * 1), 0)

            a2, b2 = compute_double(alpha, temp_list2)
            result2 = max(math.exp(a2[-1] + b2[-1] * 1) - 1, 0)

            a3, b3 = compute_double(alpha, es_list3)
            aaa = int(a3[-1] + b3[-1] * 1)
            result3 = max(temp_list3[0] + aaa, 0)

            es_predict_result[flavor] = max(0.33 * result1 + 0.33 * result2 + 0.33 * result3, 0)

        elif double_or_triple == 3:
            a1, b1, c1 = compute_triple(alpha, temp_list1)
            result1 = max(int(a1[-1] + b1[-1] * 1 + c1[-1] * (1 ** 2)), 0)

            a2, b2, c2 = compute_triple(alpha, temp_list2)
            result2 = max(math.exp(a2[-1] + b2[-1] * 1 + c2[-1] * (1 ** 2)) - 1, 0)

            a3, b3, c3 = compute_triple(alpha, es_list3)
            bbb = int(a3[-1] + b3[-1] * 1 + c3[-1] * (1 ** 2))
            result3 = max(temp_list3[0] + bbb, 0)

            es_predict_result[flavor] = max(0.33 * result1 + 0.33 * result2 + 0.33 * result3, 0)

    return es_predict_result
