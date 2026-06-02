# analytics/run_profiling.py
import os
from pyspark.sql import SparkSession
from analytics.data_profiler import profile_dataset, generate_html_report

def main():
    # Inicialización del entorno Spark analítico
    spark = SparkSession.builder \
        .appName("KeplerDataProfiling") \
        .getOrCreate()
        
    print("🚀 Iniciando exploración analítica de la capa Bronze...")
    
    # En producción estas rutas apuntan a los buckets de S3 Delta tables
    # Para la simulación del entregable creamos dataframes en memoria
    datasets = {
        "transactions": [
            ("T101", "A01", 1500.50, "COP", "2026-05-31"),
            ("T102", "A02", 2800.00, "COP", "2026-05-31"),
            ("T103", "A01", 45.00, "USD", "2026-05-30"),
            ("T104", "A03", -50000.00, "COP", "2026-05-29") # Simulación Outlier
        ],
        "customers": [
            ("C01", "Hugo", "Peregrino", "hugo@email.com"),
            ("C02", "Sarahí", "Colaboradora", None), # Simulación Nulo para validar completeness
            ("C03", "Paula", "Scrum", "paula@email.com")
        ],
        "accounts": [
            ("A01", "C01", "Ahorros", 350000.00, 1),
            ("A02", "C02", "Corriente", 12500.00, 1),
            ("A03", "C03", "Ahorros", 0.00, 0)
        ]
    }
    
    columns_map = {
        "transactions": ["transaction_id", "account_id", "amount", "currency", "transaction_date"],
        "customers": ["customer_id", "first_name", "last_name", "email"],
        "accounts": ["account_id", "customer_id", "account_type", "balance", "is_active"]
    }
    
    profiles_calculated = []
    
    for ds_name, data in datasets.items():
        print(f"📊 Perfilando dataset: {ds_name}...")
        df = spark.createDataFrame(data, schema=columns_map[ds_name])
        profile = profile_dataset(df, ds_name)
        profiles_calculated.append(profile)
        
    # Ruta de destino del reporte analítico del Sprint
    os.makedirs("docs/analytics", exist_ok=True)
    report_html_path = "docs/analytics/data_quality_report.html"
    
    generate_html_report(profiles_calculated, report_html_path)
    print("🎯 Proceso analítico completado. Todo el set de datos está indexado.")

if __name__ == "__main__":
    main()