FUTURE_LIST_NONFERROUS_METALS: list[str] = [
    "CUL9",  # 沪铜
    "ALL9",  # 沪铝
    "ZNL9",  # 沪锌
    "PBL9",  # 沪铅
    "NIL9",  # 沪镍
    "SNL9",  # 沪锡
    "AOL9",  # 氧化铝
    "SIL9",  # 工业硅
    "LCL9",  # 碳酸锂
    "PSL9",  # 多晶硅
]
"""有色金属板块"""

FUTURE_LIST_FERROUS_METALS: list[str] = [
    "RBL9",  # 螺纹钢
    "IL9",  # 铁矿石
    "HCL9",  # 热卷
    "SSL9",  # 不锈钢
    "SFL9",  # 硅铁
    "SML9",  # 锰硅
]
"""黑色金属板块"""

FUTURE_LIST_COAL: list[str] = [
    "JML9",  # 焦煤
    "JL9",  # 焦炭
]
"""煤炭板块"""

FUTURE_LIST_LIGHT_INDUSTRY: list[str] = [
    "FGL9",  # 玻璃
    "SPL9",  # 纸浆
]
"""轻工板块"""

FUTURE_LIST_PETROLEUM: list[str] = [
    "SCL9",  # 原油
    "FUL9",  # 燃料油
    "BUL9",  # 沥青
    "PGL9",  # 液化气
]
"""石油板块"""

FUTURE_LIST_CHEMICAL_INDUSTRY: list[str] = [
    "TAL9",  # PTA
    "VL9",  # PVC
    "RUL9",  # 橡胶
    "NRL9",  # 20号胶
    "LL9",  # 塑料
    "PFL9",  # 短纤
    "EGL9",  # 乙二醇
    "MAL9",  # 甲醇
    "PPL9",  # 聚丙烯
    "EBL9",  # 苯乙烯
    "URL9",  # 尿素
    "SAL9",  # 纯碱
    "PXL9",  # 对二甲苯
    "SHL9",  # 烧碱
]
"""化工板块"""

FUTURE_LIST_GREASE: list[str] = [
    "BL9",  # 豆二
    "ML9",  # 豆粕
    "YL9",  # 豆油
    "RML9",  # 菜籽粕
    "OIL9",  # 菜籽油
    "PL9",  # 棕榈油
    "PKL9",  # 花生
]
"""油脂板块"""

FUTURE_LIST_GRAIN: list[str] = [
    "CL9",  # 玉米
    "AL9",  # 豆一
    "CSL9",  # 淀粉
]
"""谷物板块"""

FUTURE_LIST_SOFT_COMMODITY: list[str] = [
    "CFL9",  # 棉花
    "SRL9",  # 白糖
]
"""软商品板块"""

FUTURE_LIST_AGRICULTURAL_SIDELINE_PRODUCTS: list[str] = [
    "JDL9",  # 鸡蛋
    "LHL9",  # 生猪
    "APL9",  # 苹果
    "CJL9",  # 红枣
]
"""农副产品板块"""

FUTURE_LIST_SHIPPING: list[str] = [
    "ECL9",  # 集运欧线
]
"""航运板块"""

FUTURE_LIST: list[str] = (FUTURE_LIST_NONFERROUS_METALS + FUTURE_LIST_FERROUS_METALS + FUTURE_LIST_COAL +
                          FUTURE_LIST_LIGHT_INDUSTRY + FUTURE_LIST_PETROLEUM + FUTURE_LIST_CHEMICAL_INDUSTRY +
                          FUTURE_LIST_GREASE + FUTURE_LIST_GRAIN + FUTURE_LIST_SOFT_COMMODITY +
                          FUTURE_LIST_AGRICULTURAL_SIDELINE_PRODUCTS + FUTURE_LIST_SHIPPING)
"""各期货品种"""
