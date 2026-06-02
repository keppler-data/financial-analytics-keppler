# airflow/tasks/schema_manager.py
import os
import json
import re
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, IntegerType
from delta.tables import DeltaTable

# Validaciones de Formatos requeridas por la especificación técnica
FORMAT_VALIDATORS = {
    "date": r"^\d{4}-\d{2}-\d{2}$",
    "datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    "currency_code": r"^[A-Z]{3}$",
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "amount": r"^\d+(\.\d{1,2})?$"
}

TYPE_MAPPING = {
    "string": StringType(),
    "integer": IntegerType(),
    "decimal(18,2)": DecimalType(18, 2),
    "decimal(5,2)": DecimalType(5, 2)
}

def load_pyspark_schema(dataset_name: str, version: str = "v1") -> StructType:
    """Carga un esquema JSON del Registry y lo convierte a StructType de PySpark"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "schema_registry", f"{dataset_name}.json")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ El dataset '{dataset_name}' no existe en el Registry.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    version_data = registry["versions"].get(version)
    if not version_data:
        raise ValueError(f"❌ Versión '{version}' no encontrada para el dataset '{dataset_name}'.")
        
    fields = []
    for field_name, props in version_data["fields"].items():
        data_type = TYPE_MAPPING.get(props["type"], StringType())
        fields.append(StructField(field_name, data_type, props["nullable"]))
        
    return StructType(fields)

def validate_schema_compatibility(current_schema, new_schema):
    """
    Verifica si el nuevo schema es compatible con el existente en el Lakehouse.
    Retorna: (is_compatible: bool, breaking_changes: list)
    """
    breaking_changes = []
    
    # Verificar columnas eliminadas (Breaking change)
    removed_cols = set(current_schema.fieldNames()) - set(new_schema.fieldNames())
    if removed_cols:
        breaking_changes.append(f"Removed columns: {removed_cols}")
        
    # Verificar cambios de tipo de datos o restricciones de nulidad (Breaking change)
    for field in current_schema.fields:
        if field.name in new_schema.fieldNames():
            new_field = new_schema[field.name]
            if field.dataType != new_field.dataType:
                breaking_changes.append(f"Type changed: {field.name} {field.dataType} -> {new_field.dataType}")
            if field.nullable and not new_field.nullable:
                breaking_changes.append(f"Constraint changed: {field.name} se volvió NOT NULL")
                
    return len(breaking_changes) == 0, breaking_changes

def apply_schema_evolution(delta_path: str, new_df, dataset_name: str, version: str = "v1"):
    """
    Aplica schema evolution usando Delta Lake merge schema de forma segura.
    Bloquea la operación ante cambios de tipo e impactos Breaking detectados.
    """
    spark = SparkSession.builder.getOrCreate()
    
    # Si la tabla ya existe físicamente en Delta Lake, validamos compatibilidad retrospectiva
    if DeltaTable.isDeltaTable(spark, delta_path):
        delta_table = DeltaTable.forPath(spark, delta_path)
        current_schema = delta_table.toDF().schema
        
        is_compatible, breaking_changes = validate_schema_compatibility(current_schema, new_df.schema)
        if not is_compatible:
            raise ValueError(f"⛔ Transacción Abortada. Cambios BREAKING detectados en {dataset_name}: {breaking_changes}")
            
    # Escritura optimizada con MergeSchema para asimilar evoluciones permisibles (No-breaking)
    print(f"🔄 Guardando datos con Schema Evolution habilitado para {dataset_name}...")
    new_df.write \
        .format("delta") \
        .option("mergeSchema", "true") \
        .mode("append") \
        .save(delta_path)
    print(f"✅ Ingesta Delta exitosa en: {delta_path}")