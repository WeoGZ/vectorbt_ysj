FUTURE_SIZE_PRECIOUS_METALS: dict[str, float] = {
    "AUL9": 1000,  # 沪金
    "AGL9": 15  # 沪银
}
"""贵金属的交易单位，XX吨/手"""

FUTURE_SIZE_NONFERROUS_METALS: dict[str, float] = {
    "CUL9": 5,  # 沪铜
    "ALL9": 5,  # 沪铝
    "ZNL9": 5,  # 沪锌
    "PBL9": 5,  # 沪铅
    "NIL9": 1,  # 沪镍
    "SNL9": 1,  # 沪锡
    "AOL9": 20,  # 氧化铝
    "SIL9": 5,  # 工业硅
    "LCL9": 1,  # 碳酸锂
    "PSL9": 3,  # 多晶硅
}
"""有色金属的交易单位，XX吨/手"""

FUTURE_SIZE_FERROUS_METALS: dict[str, float] = {
    "RBL9": 10,  # 螺纹钢
    "IL9": 100,  # 铁矿石
    "HCL9": 10,  # 热卷
    "SSL9": 5,  # 不锈钢
    "SFL9": 5,  # 硅铁
    "SML9": 5,  # 锰硅
}
"""黑色金属的交易单位，XX吨/手"""

FUTURE_SIZE_COAL: dict[str, float] = {
    "JML9": 60,  # 焦煤
    "JL9": 100,  # 焦炭
}
"""煤炭的交易单位，XX吨/手"""

FUTURE_SIZE_LIGHT_INDUSTRY: dict[str, float] = {
    "FGL9": 20,  # 玻璃
    "SPL9": 10,  # 纸浆
}
"""轻工的交易单位，XX吨/手"""

FUTURE_SIZE_PETROLEUM: dict[str, float] = {
    "SCL9": 1000,  # 原油
    "FUL9": 10,  # 燃料油
    "BUL9": 10,  # 沥青
    "PGL9": 20,  # 液化气
}
"""石油的交易单位，XX吨/手"""

FUTURE_SIZE_CHEMICAL_INDUSTRY: dict[str, float] = {
    "TAL9": 5,  # PTA
    "VL9": 5,  # PVC
    "RUL9": 10,  # 橡胶
    "NRL9": 10,  # 20号胶
    "LL9": 5,  # 塑料
    "PFL9": 5,  # 短纤
    "EGL9": 10,  # 乙二醇
    "MAL9": 10,  # 甲醇
    "PPL9": 5,  # 聚丙烯
    "EBL9": 5,  # 苯乙烯
    "URL9": 20,  # 尿素
    "SAL9": 20,  # 纯碱
    "PXL9": 5,  # 对二甲苯
    "SHL9": 30,  # 烧碱
}
"""化工的交易单位，XX吨/手"""

FUTURE_SIZE_GREASE: dict[str, float] = {
    "BL9": 10,  # 豆二
    "ML9": 10,  # 豆粕
    "YL9": 10,  # 豆油
    "RML9": 10,  # 菜籽粕
    "OIL9": 10,  # 菜籽油
    "PL9": 10,  # 棕榈油
    "PKL9": 5,  # 花生
}
"""油脂的交易单位，XX吨/手"""

FUTURE_SIZE_GRAIN: dict[str, float] = {
    "CL9": 10,  # 玉米
    "AL9": 10,  # 豆一
    "CSL9": 10,  # 淀粉
}
"""谷物的交易单位，XX吨/手"""

FUTURE_SIZE_SOFT_COMMODITY: dict[str, float] = {
    "CFL9": 5,  # 棉花
    "SRL9": 10,  # 白糖
}
"""软商品的交易单位，XX吨/手"""

FUTURE_SIZE_AGRICULTURAL_SIDELINE_PRODUCTS: dict[str, float] = {
    "JDL9": 10,  # 鸡蛋
    "LHL9": 16,  # 生猪
    "APL9": 10,  # 苹果
    "CJL9": 5,  # 红枣
}
"""农副产品的交易单位，XX吨/手"""

FUTURE_SIZE_SHIPPING: dict[str, float] = {
    "ECL9": 50,  # 集运欧线
}
"""航运的交易单位，XX吨/手"""

FUTURE_SIZE_ALL: dict[str, float] = {**FUTURE_SIZE_PRECIOUS_METALS, **FUTURE_SIZE_NONFERROUS_METALS,
                                     **FUTURE_SIZE_FERROUS_METALS, **FUTURE_SIZE_COAL,
                                     **FUTURE_SIZE_LIGHT_INDUSTRY, **FUTURE_SIZE_PETROLEUM,
                                     **FUTURE_SIZE_CHEMICAL_INDUSTRY, **FUTURE_SIZE_GREASE,
                                     **FUTURE_SIZE_GRAIN, **FUTURE_SIZE_SOFT_COMMODITY,
                                     **FUTURE_SIZE_AGRICULTURAL_SIDELINE_PRODUCTS, **FUTURE_SIZE_SHIPPING}
"""所有品种的交易单位，XX吨/手"""
