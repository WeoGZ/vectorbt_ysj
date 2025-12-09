FUTURE_SLIPPAGE_PRECIOUS_METALS: dict[str, float] = {
    "AUL9": 0.00004,  # 沪金
    "AGL9": 0.0002  # 沪银
}
"""贵金属的滑点，百分比"""

FUTURE_SLIPPAGE_NONFERROUS_METALS: dict[str, float] = {
    "CUL9": 0.0001,  # 沪铜
    "ALL9": 0.0003,  # 沪铝
    "ZNL9": 0.0003,  # 沪锌
    "PBL9": 0.0004,  # 沪铅
    "NIL9": 0.00006,  # 沪镍
    "SNL9": 0.00005,  # 沪锡
    "AOL9": 0.0003,  # 氧化铝
    "SIL9": 0.0004,  # 工业硅
    "LCL9": 0.0002,  # 碳酸锂
    "PSL9": 0.0002,  # 多晶硅
}
"""有色金属的滑点，百分比"""

FUTURE_SLIPPAGE_FERROUS_METALS: dict[str, float] = {
    "RBL9": 0.0003,  # 螺纹钢
    "IL9": 0.0006,  # 铁矿石
    "HCL9": 0.0003,  # 热卷
    "SSL9": 0.0003,  # 不锈钢
    "SFL9": 0.0002,  # 硅铁
    "SML9": 0.0002,  # 锰硅
}
"""黑色金属的滑点，百分比"""

FUTURE_SLIPPAGE_COAL: dict[str, float] = {
    "JML9": 0.0003,  # 焦煤
    "JL9": 0.0002,  # 焦炭
}
"""煤炭的滑点，百分比"""

FUTURE_SLIPPAGE_LIGHT_INDUSTRY: dict[str, float] = {
    "FGL9": 0.0006,  # 玻璃
    "SPL9": 0.0004,  # 纸浆
}
"""轻工的滑点，百分比"""

FUTURE_SLIPPAGE_PETROLEUM: dict[str, float] = {
    "SCL9": 0.0003,  # 原油
    "FUL9": 0.0004,  # 燃料油
    "BUL9": 0.0004,  # 沥青
    "PGL9": 0.0003,  # 液化气
}
"""石油的滑点，百分比"""

FUTURE_SLIPPAGE_CHEMICAL_INDUSTRY: dict[str, float] = {
    "TAL9": 0.0004,  # PTA
    "VL9": 0.0002,  # PVC
    "RUL9": 0.0004,  # 橡胶
    "NRL9": 0.0005,  # 20号胶
    "LL9": 0.0002,  # 塑料
    "PFL9": 0.0003,  # 短纤
    "EGL9": 0.0003,  # 乙二醇
    "MAL9": 0.0004,  # 甲醇
    "PPL9": 0.0002,  # 聚丙烯
    "EBL9": 0.0002,  # 苯乙烯
    "URL9": 0.0005,  # 尿素
    "SAL9": 0.0005,  # 纯碱
    "PXL9": 0.0003,  # 对二甲苯
    "SHL9": 0.0004,  # 烧碱
}
"""化工的滑点，百分比"""

FUTURE_SLIPPAGE_GREASE: dict[str, float] = {
    "BL9": 0.0003,  # 豆二
    "ML9": 0.0004,  # 豆粕
    "YL9": 0.0003,  # 豆油
    "RML9": 0.0004,  # 菜籽粕
    "OIL9": 0.0002,  # 菜籽油
    "PL9": 0.0003,  # 棕榈油
    "PKL9": 0.0003,  # 花生
}
"""油脂的滑点，百分比"""

FUTURE_SLIPPAGE_GRAIN: dict[str, float] = {
    "CL9": 0.0005,  # 玉米
    "AL9": 0.0003,  # 豆一
    "CSL9": 0.0004,  # 淀粉
}
"""谷物的滑点，百分比"""

FUTURE_SLIPPAGE_SOFT_COMMODITY: dict[str, float] = {
    "CFL9": 0.0004,  # 棉花
    "SRL9": 0.0002,  # 白糖
}
"""软商品的滑点，百分比"""

FUTURE_SLIPPAGE_AGRICULTURAL_SIDELINE_PRODUCTS: dict[str, float] = {
    "JDL9": 0.0003,  # 鸡蛋
    "LHL9": 0.0003,  # 生猪
    "APL9": 0.0002,  # 苹果
    "CJL9": 0.0005,  # 红枣
}
"""农副产品的滑点，百分比"""

FUTURE_SLIPPAGE_SHIPPING: dict[str, float] = {
    "ECL9": 0.0001,  # 集运欧线
}
"""航运的滑点，百分比"""

FUTURE_SLIPPAGE_ALL: dict[str, float] = {**FUTURE_SLIPPAGE_PRECIOUS_METALS, **FUTURE_SLIPPAGE_NONFERROUS_METALS,
                                         **FUTURE_SLIPPAGE_FERROUS_METALS, **FUTURE_SLIPPAGE_COAL,
                                         **FUTURE_SLIPPAGE_LIGHT_INDUSTRY, **FUTURE_SLIPPAGE_PETROLEUM,
                                         **FUTURE_SLIPPAGE_CHEMICAL_INDUSTRY, **FUTURE_SLIPPAGE_GREASE,
                                         **FUTURE_SLIPPAGE_GRAIN, **FUTURE_SLIPPAGE_SOFT_COMMODITY,
                                         **FUTURE_SLIPPAGE_AGRICULTURAL_SIDELINE_PRODUCTS, **FUTURE_SLIPPAGE_SHIPPING}
"""所有品种的滑点，百分比"""
