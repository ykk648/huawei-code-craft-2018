## 题目要求

[赛题在这里][1]

## 解释说明

程序使用pure python，不借助任何第三方库（包括numpy）。

## 文件目录结构

### 主程序
[主程序入口][2]
[预测主程序][4]
[old预测主程序][3]
[工具库][5] 包括：
- 一些numpy算法
- 拉格朗日均值
- 数据差分算法
- 旧的装箱算法（首次适应和多重背包）

### 预测算法
[ExponentialSmooth.py][6] ———— 二次三次指数平滑
[LinearRegression.py][7] ———— 一元二元线性回归
[RandomForestRegression.py][8] ———— 随机森林回归
[SimulateAnneal.py][9] ———— 模拟退火（用于对预测出来的虚拟机部署）


  [1]: http://codecraft.devcloud.huaweicloud.com/home/detail
  [2]: https://github.com/cloisonne/huawei-2018-software/blob/master/ecs.py
  [3]: https://github.com/cloisonne/huawei-2018-software/blob/master/predict_magic.py
  [4]: https://github.com/cloisonne/huawei-2018-software/blob/master/predictor.py
  [5]: https://github.com/cloisonne/huawei-2018-software/blob/master/tool_lib.py
  [6]: https://github.com/cloisonne/huawei-2018-software/blob/master/ExponentialSmooth.py
  [7]: https://github.com/cloisonne/huawei-2018-software/blob/master/LinearRegression.py
  [8]: https://github.com/cloisonne/huawei-2018-software/blob/master/RandomForestRegression.py
  [9]: https://github.com/cloisonne/huawei-2018-software/blob/master/SimulateAnneal.py