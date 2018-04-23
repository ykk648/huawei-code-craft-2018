# -*- coding: utf-8 -*-


def compute_error(w, data):
    error_count = 0
    for i in range(len(data)):
        x = [1] + data[i][:len(data[i]) - 1]
        y = data[i][-1]
        error_count = error_count + (w_mul_x(w, x) - y) ** 2
    return error_count / (2 * len(data))


def w_mul_x(w, x):
    sum_wx = 0
    for (i, j) in zip(w, x):
        sum_wx = sum_wx + i * j
    return sum_wx


def compute_gradient(w, data, learning_rate):
    w_temp = [0 for i in range(len(w))]
    partial_diff = [0 for j in range(0, len(data))]
    for j in range(0, len(w)):
        for i in range(0, len(data)):
            x = data[i][:len(data[i]) - 1]
            x = x + [u * u for u in x]
            y = data[i][-1]
            max_x = max(x)
            min_x = min(x)
            if max_x - min_x > 0:
                x = [1] + [(h - (sum(x) / len(x))) / (max_x - min_x) for h in x]
            else:
                x = [1] + x
            partial_diff[i] = (w_mul_x(w, x) - y) * x[j]
        w_temp[j] = w[j] - learning_rate * sum(partial_diff) / len(data)
    w = w_temp
    return w


def linear_regression(w_initial, data, learning_rate, iterations):
    w = w_initial
    for i in range(iterations):
        w = compute_gradient(w, data, learning_rate)
    return w
