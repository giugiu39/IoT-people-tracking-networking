import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Caricamento dei dati
file_path = "edge_ai/output/events.jsonl"
try:
    df = pd.read_json(file_path, lines=True)
except FileNotFoundError:
    print(f"Errore: File {file_path} non trovato.")
    exit()

# 2. Definizione delle funzioni per i percentili
def p95(x):
    return x.quantile(0.95)

def p99(x):
    return x.quantile(0.99)

# 3. Calcolo delle statistiche aggregate
stats = df.groupby('path')['latency_ms'].agg(
    Count='count',
    Mean='mean',
    Median='median',
    Std_Dev='std',
    Min='min',
    Max='max',
    P95=p95,
    P99=p99
).round(2)

print("\n=================================================================")
print(" STATISTICHE DI LATENZA END-TO-END (ms) PER PATH DI COMUNICAZIONE")
print("=================================================================")
print(stats.to_string())
print("=================================================================\n")

# 4. Configurazione dello stile dei grafici
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("Analisi Comparativa della Latenza: CoAP+WIFI vs BLE+MQTT ", fontsize=16, fontweight='bold')

# Grafico 1: Boxplot per la distribuzione e gli outlier
sns.boxplot(
    ax=axes[0], 
    x='path', 
    y='latency_ms', 
    data=df, 
    palette={"CoAP": "#1f77b4", "BLE_MQTT": "#d62728"}
)
axes[0].set_title("Distribuzione della Latenza", fontsize=14)
axes[0].set_xlabel("Communication Path", fontsize=12)
axes[0].set_ylabel("End-to-End Latency (ms)", fontsize=12)

# Grafico 2: Scatterplot per l'andamento sequenziale degli eventi
sns.scatterplot(
    ax=axes[1], 
    x='event_id', 
    y='latency_ms', 
    hue='path', 
    data=df, 
    palette={"CoAP": "#1f77b4", "BLE_MQTT": "#d62728"},
    alpha=0.7
)
axes[1].set_title("Andamento della Latenza per Evento", fontsize=14)
axes[1].set_xlabel("Event ID", fontsize=12)
axes[1].set_ylabel("End-to-End Latency (ms)", fontsize=12)

plt.tight_layout()
plt.savefig("latency_analysis.png", dpi=300)
print("[Analisi Completata] Il grafico è stato salvato come 'latency_analysis.png'.")
plt.show()