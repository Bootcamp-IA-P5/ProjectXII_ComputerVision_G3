
import os
import yaml
import glob
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configuración
DATA_YAML = "/workspace/dataset_yolov8/data.yaml"
TRAIN_DIR = "/workspace/dataset_yolov8/train/labels"

def analyze_dataset():
    print(f"📂 Analizando dataset en: {TRAIN_DIR}...")
    
    # 1. Leer nombres convertidos de clases
    if not os.path.exists(DATA_YAML):
        print("❌ No se encontró data.yaml")
        return

    with open(DATA_YAML, 'r') as f:
        data_config = yaml.safe_load(f)
        class_names = data_config['names']
        
    print(f"ℹ️  Total de clases definidas: {len(class_names)}")

    # 2. Contar ocurrencias en etiquetas
    label_files = glob.glob(os.path.join(TRAIN_DIR, "*.txt"))
    class_counts = Counter()
    total_files = len(label_files)
    
    print(f"ℹ️  Total de imágenes de entrenamiento: {total_files}")
    
    for lf in label_files:
        with open(lf, 'r') as f:
            lines = f.readlines()
            for line in lines:
                try:
                    class_id = int(line.split()[0])
                    class_counts[class_id] += 1
                except:
                    pass

    # 3. Crear DataFrame
    data = []
    for cid, count in class_counts.items():
        name = class_names[cid] if cid < len(class_names) else f"Unknown-{cid}"
        data.append({"Class ID": cid, "Name": name, "Count": count})
    
    # Añadir clases con 0 imágenes
    found_ids = set(class_counts.keys())
    for cid in range(len(class_names)):
        if cid not in found_ids:
            data.append({"Class ID": cid, "Name": class_names[cid], "Count": 0})
            
    df = pd.DataFrame(data).sort_values("Count", ascending=False)
    
    # 4. Mostrar estadísticas
    print("\n" + "="*50)
    print("📊 ESTADÍSTICAS DEL DATASET")
    print("="*50)
    print(df.describe())
    
    print("\n🔻 TOP 10 CLASES CON MENOS DATOS:")
    print(df.tail(10)[['Name', 'Count']].to_string(index=False))
    
    print("\n🔺 TOP 10 CLASES CON MÁS DATOS:")
    print(df.head(10)[['Name', 'Count']].to_string(index=False))
    
    # 5. Recomendación de corte
    print("\n" + "="*50)
    print("💡 ANÁLISIS DE CORTE")
    print("="*50)
    
    cuts = [10, 20, 50, 100]
    for c in cuts:
        valid_classes = df[df['Count'] >= c]
        print(f"• Si filtras clases con < {c} imágenes:")
        print(f"  ➜ Te quedarías con {len(valid_classes)} clases (de {len(class_names)})")

if __name__ == "__main__":
    analyze_dataset()
