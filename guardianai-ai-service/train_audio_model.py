import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import librosa

# --- 1. Load the VGGish Model ---
print("Loading VGGish model...")
vggish_model = hub.load('https://tfhub.dev/google/vggish/1')
print("✅ VGGish model loaded.")

# --- 2. Function to Extract Features from an Audio File ---
def extract_vggish_features(audio_path):
    try:
        # Load audio and resample to 16kHz as required by VGGish
        waveform, sr = librosa.load(audio_path, sr=16000, mono=True)
        # VGGish returns a feature vector for each 0.96s chunk of audio.
        # We'll take the average across all chunks.
        features = vggish_model(waveform)
        return np.mean(features.numpy(), axis=0)
    except Exception as e:
        print(f"Error processing {audio_path}: {e}")
        return None

# --- 3. Prepare the Dataset ---
DATASET_PATH = "dataset"
X, y = [], []
labels = {"normal": 0, "screams": 1}

# Check if dataset directory exists
if not os.path.exists(DATASET_PATH):
    print(f"❌ Error: 'dataset' directory not found. Please create it and add 'screams' and 'normal' subfolders with audio files.")
    exit()

print("Extracting features from dataset...")
for folder_name, label in labels.items():
    folder_path = os.path.join(DATASET_PATH, folder_name)
    if not os.path.exists(folder_path):
        print(f"⚠️ Warning: Folder '{folder_name}' not found in 'dataset'. Skipping.")
        continue
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        features = extract_vggish_features(file_path)
        if features is not None:
            X.append(features)
            y.append(label)

if not X:
    print("❌ Error: No audio files were successfully processed. Please check your 'dataset' folder.")
    exit()

X = np.array(X)
y = np.array(y)

# --- 4. Train the SVM Classifier ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Scale the features for better performance
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\nTraining SVM classifier...")
# 'C=10' and 'gamma=0.1' are good starting points for tuning
svm_model = SVC(kernel='rbf', C=10, gamma=0.1, probability=True)
svm_model.fit(X_train_scaled, y_train)

# --- 5. Evaluate the Model ---
print("\nEvaluating model performance:")
predictions = svm_model.predict(X_test_scaled)
print(classification_report(y_test, predictions, target_names=labels.keys()))

# --- 6. Save the Trained Model and the Scaler ---
joblib.dump(svm_model, 'scream_classifier.pkl')
joblib.dump(scaler, 'scaler.pkl')
print("\n✅ Model and scaler saved successfully as 'scream_classifier.pkl' and 'scaler.pkl'.")