FUTURE_MARGIN_RATIO_PRECIOUS_METALS: dict[str, float] = {
    "AUL9": 27,  # 沪金
    "AGL9": 27  # 沪银
}
"""贵金属的保证金比例，%"""

FUTURE_MARGIN_RATIO_NONFERROUS_METALS: dict[str, float] = {
    "CUL9": 16,  # 沪铜
    "ALL9": 15,  # 沪铝
    "ZNL9": 16,  # 沪锌
    "PBL9": 16,  # 沪铅
    "NIL9": 18,  # 沪镍
    "SNL9": 17,  # 沪锡
    "AOL9": 16,  # 氧化铝
    "SIL9": 15,  # 工业硅
    "LCL9": 19,  # 碳酸锂
    "PSL9": 21,  # 多晶硅
}
"""有色金属的保证金比例，%"""

FUTURE_MARGIN_RATIO_FERROUS_METALS: dict[str, float] = {
    "RBL9": 13,  # 螺纹钢
    "IL9": 17,  # 铁矿石
    "HCL9": 13,  # 热卷
    "SSL9": 13,  # 不锈钢
    "SFL9": 15,  # 硅铁
    "SML9": 16,  # 锰硅
}
"""黑色金属的保证金比例，%"""

FUTURE_MARGIN_RATIO_COAL: dict[str, float] = {
    "JML9": 18,  # 焦煤
    "JL9": 25,  # 焦炭
}
"""煤炭的保证金比例，%"""

FUTURE_MARGIN_RATIO_LIGHT_INDUSTRY: dict[str, float] = {
    "FGL9": 18,  # 玻璃
    "SPL9": 12,  # 纸浆
}
"""轻工的保证金比例，%"""

FUTURE_MARGIN_RATIO_PETROLEUM: dict[str, float] = {
    "SCL9": 18,  # 原油
    "FUL9": 16,  # 燃料油
    "BUL9": 16,  # 沥青
    "PGL9": 15,  # 液化气
}
"""石油的保证金比例，%"""

FUTURE_MARGIN_RATIO_CHEMICAL_INDUSTRY: dict[str, float] = {
    "TAL9": 16,  # PTA
    "VL9": 13,  # PVC
    "RUL9": 17,  # 橡胶
    "NRL9": 16,  # 20号胶
    "LL9": 13,  # 塑料
    "PFL9": 13,  # 短纤
    "EGL9": 15,  # 乙二醇
    "MAL9": 13,  # 甲醇
    "PPL9": 13,  # 聚丙烯
    "EBL9": 15,  # 苯乙烯
    "URL9": 14,  # 尿素
    "SAL9": 17,  # 纯碱
    "PXL9": 14,  # 对二甲苯
    "SHL9": 14,  # 烧碱
}
"""化工的保证金比例，%"""

FUTURE_MARGIN_RATIO_GREASE: dict[str, float] = {
    "BL9": 12,  # 豆二
    "ML9": 13,  # 豆粕
    "YL9": 13,  # 豆油
    "RML9": 14,  # 菜籽粕
    "OIL9": 14,  # 菜籽油
    "PL9": 15,  # 棕榈油
    "PKL9": 13,  # 花生
}
"""油脂的保证金比例，%"""

FUTURE_MARGIN_RATIO_GRAIN: dict[str, float] = {
    "CL9": 12,  # 玉米
    "AL9": 12,  # 豆一
    "CSL9": 11,  # 淀粉
}
"""谷物的保证金比例，%"""

FUTURE_MARGIN_RATIO_SOFT_COMMODITY: dict[str, float] = {
    "CFL9": 14,  # 棉花
    "SRL9": 13,  # 白糖
}
"""软商品的保证金比例，%"""

FUTURE_MARGIN_RATIO_AGRICULTURAL_SIDELINE_PRODUCTS: dict[str, float] = {
    "JDL9": 12,  # 鸡蛋
    "LHL9": 13,  # 生猪
    "APL9": 17,  # 苹果
    "CJL9": 14,  # 红枣
}
"""农副产品的保证金比例，%"""

FUTURE_MARGIN_RATIO_SHIPPING: dict[str, float] = {
    "ECL9": 28,  # 集运欧线
}
"""航运的保证金比例，%"""

FUTURE_MARGIN_RATIO_ALL: dict[str, float] = {**FUTURE_MARGIN_RATIO_PRECIOUS_METALS,
                                             **FUTURE_MARGIN_RATIO_NONFERROUS_METALS,
                                             **FUTURE_MARGIN_RATIO_FERROUS_METALS, **FUTURE_MARGIN_RATIO_COAL,
                                             **FUTURE_MARGIN_RATIO_LIGHT_INDUSTRY, **FUTURE_MARGIN_RATIO_PETROLEUM,
                                             **FUTURE_MARGIN_RATIO_CHEMICAL_INDUSTRY, **FUTURE_MARGIN_RATIO_GREASE,
                                             **FUTURE_MARGIN_RATIO_GRAIN, **FUTURE_MARGIN_RATIO_SOFT_COMMODITY,
                                             **FUTURE_MARGIN_RATIO_AGRICULTURAL_SIDELINE_PRODUCTS,
                                             **FUTURE_MARGIN_RATIO_SHIPPING}
"""所有品种的保证金比例，%"""
