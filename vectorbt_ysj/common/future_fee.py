FUTURE_FEE_PRECIOUS_METALS: dict[str, float] = {
    "AUL9": 0.000025,  # 沪金
    "AGL9": 0.00015  # 沪银
}
"""贵金属的交易手续费，百分比"""

FUTURE_FEE_NONFERROUS_METALS: dict[str, float] = {
    "CUL9": 0.0001,  # 沪铜
    "ALL9": 0.00004,  # 沪铝
    "ZNL9": 0.00004,  # 沪锌
    "PBL9": 0.00008,  # 沪铅
    "NIL9": 0.00002,  # 沪镍
    "SNL9": 0.000015,  # 沪锡
    "AOL9": 0.0002,  # 氧化铝
    "SIL9": 0.0001,  # 工业硅
    "LCL9": 0.0002,  # 碳酸锂
    "PSL9": 0.0002,  # 多晶硅
}
"""有色金属的交易手续费，百分比"""

FUTURE_FEE_FERROUS_METALS: dict[str, float] = {
    "RBL9": 0.0002,  # 螺纹钢
    "IL9": 0.0002,  # 铁矿石
    "HCL9": 0.00015,  # 热卷
    "SSL9": 0.0001,  # 不锈钢
    "SFL9": 0.0001,  # 硅铁
    "SML9": 0.0001,  # 锰硅
}
"""黑色金属的交易手续费，百分比"""

FUTURE_FEE_COAL: dict[str, float] = {
    "JML9": 0.0003,  # 焦煤
    "JL9": 0.00022,  # 焦炭
}
"""煤炭的交易手续费，百分比"""

FUTURE_FEE_LIGHT_INDUSTRY: dict[str, float] = {
    "FGL9": 0.0002,  # 玻璃
    "SPL9": 0.0001,  # 纸浆
}
"""轻工的交易手续费，百分比"""

FUTURE_FEE_PETROLEUM: dict[str, float] = {
    "SCL9": 0.00005,  # 原油
    "FUL9": 0.00015,  # 燃料油
    "BUL9": 0.0001,  # 沥青
    "PGL9": 0.0001,  # 液化气
}
"""石油的交易手续费，百分比"""

FUTURE_FEE_CHEMICAL_INDUSTRY: dict[str, float] = {
    "TAL9": 0.00015,  # PTA
    "VL9": 0.00005,  # PVC
    "RUL9": 0.00003,  # 橡胶
    "NRL9": 0.00003,  # 20号胶
    "LL9": 0.00006,  # 塑料
    "PFL9": 0.00007,  # 短纤
    "EGL9": 0.00007,  # 乙二醇
    "MAL9": 0.00015,  # 甲醇
    "PPL9": 0.00005,  # 聚丙烯
    "EBL9": 0.0001,  # 苯乙烯
    "URL9": 0.00015,  # 尿素
    "SAL9": 0.0003,  # 纯碱
    "PXL9": 0.00015,  # 对二甲苯
    "SHL9": 0.00015,  # 烧碱
}
"""化工的交易手续费，百分比"""

FUTURE_FEE_GREASE: dict[str, float] = {
    "BL9": 0.00005,  # 豆二
    "ML9": 0.00006,  # 豆粕
    "YL9": 0.00005,  # 豆油
    "RML9": 0.00007,  # 菜籽粕
    "OIL9": 0.00002,  # 菜籽油
    "PL9": 0.00005,  # 棕榈油
    "PKL9": 0.00008,  # 花生
}
"""油脂的交易手续费，百分比"""

FUTURE_FEE_GRAIN: dict[str, float] = {
    "CL9": 0.00009,  # 玉米
    "AL9": 0.00007,  # 豆一
    "CSL9": 0.00008,  # 淀粉
}
"""谷物的交易手续费，百分比"""

FUTURE_FEE_SOFT_COMMODITY: dict[str, float] = {
    "CFL9": 0.00007,  # 棉花
    "SRL9": 0.00007,  # 白糖
}
"""软商品的交易手续费，百分比"""

FUTURE_FEE_AGRICULTURAL_SIDELINE_PRODUCTS: dict[str, float] = {
    "JDL9": 0.00025,  # 鸡蛋
    "LHL9": 0.00015,  # 生猪
    "APL9": 0.00015,  # 苹果
    "CJL9": 0.00006,  # 红枣
}
"""农副产品的交易手续费，百分比"""

FUTURE_FEE_SHIPPING: dict[str, float] = {
    "ECL9": 0.001,  # 集运欧线
}
"""航运的交易手续费，百分比"""

FUTURE_FEE_ALL: dict[str, float] = {**FUTURE_FEE_PRECIOUS_METALS, **FUTURE_FEE_NONFERROUS_METALS,
                                    **FUTURE_FEE_FERROUS_METALS, **FUTURE_FEE_COAL,
                                    **FUTURE_FEE_LIGHT_INDUSTRY, **FUTURE_FEE_PETROLEUM,
                                    **FUTURE_FEE_CHEMICAL_INDUSTRY, **FUTURE_FEE_GREASE,
                                    **FUTURE_FEE_GRAIN, **FUTURE_FEE_SOFT_COMMODITY,
                                    **FUTURE_FEE_AGRICULTURAL_SIDELINE_PRODUCTS, **FUTURE_FEE_SHIPPING}
"""所有品种的交易手续费，百分比"""
