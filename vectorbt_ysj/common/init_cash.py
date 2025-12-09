"""vbt不支持保证金制度，因此暂定是文华回测初始资金参数的6倍"""

INIT_CASH_PRECIOUS_METALS: dict[str, float] = {
    "AUL9": 900000,  # 沪金
    "AGL9": 270000  # 沪银
}
"""贵金属的起始资金"""

INIT_CASH_NONFERROUS_METALS: dict[str, float] = {
    "CUL9": 450000,  # 沪铜
    "ALL9": 150000,  # 沪铝
    "ZNL9": 180000,  # 沪锌
    "PBL9": 180000,  # 沪铅
    "NIL9": 270000,  # 沪镍
    "SNL9": 420000,  # 沪锡
    "AOL9": 120000,  # 氧化铝
    "SIL9": 120000,  # 工业硅
    "LCL9": 240000,  # 碳酸锂
    "PSL9": 240000,  # 多晶硅
}
"""有色金属的起始资金"""

INIT_CASH_FERROUS_METALS: dict[str, float] = {
    "RBL9": 90000,  # 螺纹钢
    "IL9": 150000,  # 铁矿石
    "HCL9": 90000,  # 热卷
    "SSL9": 120000,  # 不锈钢
    "SFL9": 60000,  # 硅铁
    "SML9": 60000,  # 锰硅
}
"""黑色金属的起始资金"""

INIT_CASH_COAL: dict[str, float] = {
    "JML9": 300000,  # 焦煤
    "JL9": 480000,  # 焦炭
}
"""煤炭的起始资金"""

INIT_CASH_LIGHT_INDUSTRY: dict[str, float] = {
    "FGL9": 90000,  # 玻璃
    "SPL9": 90000,  # 纸浆
}
"""轻工的起始资金"""

INIT_CASH_PETROLEUM: dict[str, float] = {
    "SCL9": 810000,  # 原油
    "FUL9": 60000,  # 燃料油
    "BUL9": 60000,  # 沥青
    "PGL9": 150000,  # 液化气
}
"""石油的起始资金"""

INIT_CASH_CHEMICAL_INDUSTRY: dict[str, float] = {
    "TAL9": 90000,  # PTA
    "VL9": 90000,  # PVC
    "RUL9": 240000,  # 橡胶
    "NRL9": 180000,  # 20号胶
    "LL9": 90000,  # 塑料
    "PFL9": 60000,  # 短纤
    "EGL9": 90000,  # 乙二醇
    "MAL9": 90000,  # 甲醇
    "PPL9": 90000,  # 聚丙烯
    "EBL9": 60000,  # 苯乙烯
    "URL9": 60000,  # 尿素
    "SAL9": 90000,  # 纯碱
    "PXL9": 60000,  # 对二甲苯
    "SHL9": 120000,  # 烧碱
}
"""化工的起始资金"""

INIT_CASH_GREASE: dict[str, float] = {
    "BL9": 90000,  # 豆二
    "ML9": 45000,  # 豆粕
    "YL9": 120000,  # 豆油
    "RML9": 60000,  # 菜籽粕
    "OIL9": 150000,  # 菜籽油
    "PL9": 150000,  # 棕榈油
    "PKL9": 90000,  # 花生
}
"""油脂的起始资金"""

INIT_CASH_GRAIN: dict[str, float] = {
    "CL9": 30000,  # 玉米
    "AL9": 90000,  # 豆一
    "CSL9": 48000,  # 淀粉
}
"""谷物的起始资金"""

INIT_CASH_SOFT_COMMODITY: dict[str, float] = {
    "CFL9": 150000,  # 棉花
    "SRL9": 90000,  # 白糖
}
"""软商品的起始资金"""

INIT_CASH_AGRICULTURAL_SIDELINE_PRODUCTS: dict[str, float] = {
    "JDL9": 90000,  # 鸡蛋
    "LHL9": 600000,  # 生猪
    "APL9": 150000,  # 苹果
    "CJL9": 90000,  # 红枣
}
"""农副产品的起始资金"""

INIT_CASH_SHIPPING: dict[str, float] = {
    "ECL9": 210000,  # 集运欧线
}
"""航运的起始资金"""

INIT_CASH_ALL: dict[str, float] = {**INIT_CASH_PRECIOUS_METALS, **INIT_CASH_NONFERROUS_METALS,
                                   **INIT_CASH_FERROUS_METALS, **INIT_CASH_COAL,
                                   **INIT_CASH_LIGHT_INDUSTRY, **INIT_CASH_PETROLEUM,
                                   **INIT_CASH_CHEMICAL_INDUSTRY, **INIT_CASH_GREASE,
                                   **INIT_CASH_GRAIN, **INIT_CASH_SOFT_COMMODITY,
                                   **INIT_CASH_AGRICULTURAL_SIDELINE_PRODUCTS, **INIT_CASH_SHIPPING}
"""所有品种的起始资金"""
