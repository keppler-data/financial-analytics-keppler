# -*- coding: utf-8 -*-
"""
Schema explícitos para datasets Bronze
Esto garantiza que Spark no "infiera" tipos incorrectos y detecte cambios de esquema
"""

from pyspark.sql.types import (
    StructType, StructField, 
    StringType, IntegerType, DoubleType, 
    TimestampType, BooleanType
)

# ====================================================
# SCHEMA: Application (Home Credit Default Risk)
# ====================================================
APPLICATION_SCHEMA = StructType([
    StructField("SK_ID_CURR", IntegerType(), False),  # Unique ID
    StructField("TARGET", IntegerType(), True),       # Default: 0=no, 1=yes
    StructField("CODE_GENDER", StringType(), True),   # M/F
    StructField("FLAG_OWN_CAR", StringType(), True),  # Y/N
    StructField("FLAG_OWN_REALTY", StringType(), True),  # Y/N
    StructField("CNT_CHILDREN", IntegerType(), True),
    StructField("AMT_INCOME_TOTAL", DoubleType(), True),
    StructField("AMT_CREDIT", DoubleType(), True),
    StructField("AMT_ANNUITY", DoubleType(), True),
    StructField("AMT_GOODS_PRICE", DoubleType(), True),
    StructField("NAME_TYPE_SUITE", StringType(), True),
    StructField("NAME_INCOME_TYPE", StringType(), True),
    StructField("NAME_EDUCATION_TYPE", StringType(), True),
    StructField("NAME_FAMILY_STATUS", StringType(), True),
    StructField("NAME_HOUSING_TYPE", StringType(), True),
    StructField("REGION_POPULATION_RELATIVE", DoubleType(), True),
    StructField("DAYS_BIRTH", IntegerType(), True),
    StructField("DAYS_EMPLOYED", IntegerType(), True),
    StructField("DAYS_REGISTRATION", IntegerType(), True),
    StructField("DAYS_ID_PUBLISH", IntegerType(), True),
    StructField("OWN_CAR_AGE", DoubleType(), True),
    StructField("FLAG_MOBIL", IntegerType(), True),
    StructField("FLAG_EMP_PHONE", IntegerType(), True),
    StructField("FLAG_PHONE", IntegerType(), True),
    StructField("FLAG_EMAIL", IntegerType(), True),
    StructField("OCCUPATION_TYPE", StringType(), True),
    StructField("CNT_FAM_MEMBERS", DoubleType(), True),
    StructField("REGION_RATING_CLIENT", IntegerType(), True),
    StructField("REGION_RATING_CLIENT_W_CITY", IntegerType(), True),
    StructField("WEEKDAY_APPR_PROCESS_START", StringType(), True),
    StructField("HOUR_APPR_PROCESS_START", IntegerType(), True),
    StructField("REG_REGION_NOT_LIVE_REGION", IntegerType(), True),
    StructField("REG_REGION_NOT_WORK_REGION", IntegerType(), True),
    StructField("LIVE_REGION_NOT_WORK_REGION", IntegerType(), True),
    StructField("REG_CITY_NOT_LIVE_CITY", IntegerType(), True),
    StructField("REG_CITY_NOT_WORK_CITY", IntegerType(), True),
    StructField("LIVE_CITY_NOT_WORK_CITY", IntegerType(), True),
    StructField("ORGANIZATION_TYPE", StringType(), True),
    StructField("EXT_SOURCE_1", DoubleType(), True),
    StructField("EXT_SOURCE_2", DoubleType(), True),
    StructField("EXT_SOURCE_3", DoubleType(), True),
    StructField("APARTMENTS_AVG", DoubleType(), True),
    StructField("BASEMENTAREA_AVG", DoubleType(), True),
    StructField("YEARS_BEGINEXP_AVG", DoubleType(), True),
    StructField("YEARS_BUILD_AVG", DoubleType(), True),
    StructField("COMMONAREA_AVG", DoubleType(), True),
    StructField("ELEVATORS_AVG", DoubleType(), True),
    StructField("ENTRANCES_AVG", DoubleType(), True),
    StructField("FLOORSMAX_AVG", DoubleType(), True),
    StructField("FLOORSMIN_AVG", DoubleType(), True),
    StructField("LANDAREA_AVG", DoubleType(), True),
    StructField("LIVINGAPARTMENTS_AVG", DoubleType(), True),
    StructField("LIVINGAREA_AVG", DoubleType(), True),
    StructField("NONLIVINGAPARTMENTS_AVG", DoubleType(), True),
    StructField("NONLIVINGAREA_AVG", DoubleType(), True),
    StructField("APARTMENTS_MODE", DoubleType(), True),
    StructField("BASEMENTAREA_MODE", DoubleType(), True),
    StructField("YEARS_BEGINEXP_MODE", DoubleType(), True),
    StructField("YEARS_BUILD_MODE", DoubleType(), True),
    StructField("COMMONAREA_MODE", DoubleType(), True),
    StructField("ELEVATORS_MODE", DoubleType(), True),
    StructField("ENTRANCES_MODE", DoubleType(), True),
    StructField("FLOORSMAX_MODE", DoubleType(), True),
    StructField("FLOORSMIN_MODE", DoubleType(), True),
    StructField("LANDAREA_MODE", DoubleType(), True),
    StructField("LIVINGAPARTMENTS_MODE", DoubleType(), True),
    StructField("LIVINGAREA_MODE", DoubleType(), True),
    StructField("NONLIVINGAPARTMENTS_MODE", DoubleType(), True),
    StructField("NONLIVINGAREA_MODE", DoubleType(), True),
])

# ====================================================
# SCHEMA: Bureau (Histórico de créditos)
# ====================================================
BUREAU_SCHEMA = StructType([
    StructField("SK_ID_CURR", IntegerType(), False),
    StructField("SK_ID_BUREAU", IntegerType(), False),
    StructField("CREDIT_ACTIVE", StringType(), True),  # Active/Closed
    StructField("CREDIT_CURRENCY", StringType(), True),  # currency
    StructField("AMT_CREDIT_MAX_OVERDUE", DoubleType(), True),
    StructField("AMT_CREDIT_SUM", DoubleType(), True),
    StructField("AMT_CREDIT_SUM_DEBT", DoubleType(), True),
    StructField("AMT_CREDIT_SUM_LIMIT", DoubleType(), True),
    StructField("AMT_CREDIT_SUM_OVERDUE", DoubleType(), True),
    StructField("CREDIT_DAY_OVERDUE", IntegerType(), True),
    StructField("CREDIT_TYPE", StringType(), True),
    StructField("DAYS_CREDIT", IntegerType(), True),
    StructField("DAYS_CREDIT_ENDDATE", IntegerType(), True),
    StructField("DAYS_CREDIT_UPDATE", IntegerType(), True),
    StructField("MONTHS_BALANCE_MAX_BALANCE", DoubleType(), True),
    StructField("MONTHS_BALANCE_MIN_BALANCE", DoubleType(), True),
    StructField("MONTHS_BALANCE_NUM_RECORDS", IntegerType(), True),
])
