"""
Machine Learning integration for AI-powered threat detection in ClamAV GUI.
Uses feature extraction and ML models to enhance threat detection beyond traditional signatures.
"""
import os
import json
import logging
import hashlib
import struct
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML features will be disabled.")

logger = logging.getLogger(__name__)


class MLThreatDetector:
    """Machine Learning-based threat detection system."""

    def __init__(self, model_path: str = None):
        """Initialize the ML threat detector.

        Args:
            model_path: Path to save/load the ML model (default: user's AppData/ClamAV/ml_model.pkl)
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("ML features disabled due to missing scikit-learn")
            self.model = None
            self.vectorizer = None
            return

        if model_path is None:
            app_data = os.getenv('APPDATA') if os.name == 'nt' else os.path.expanduser('~')
            clamav_dir = os.path.join(app_data, 'ClamAV')
            os.makedirs(clamav_dir, exist_ok=True)
            self.model_path = os.path.join(clamav_dir, 'ml_model.pkl')
        else:
            self.model_path = model_path

        self.model = None
        self.vectorizer = None
        self.feature_names = []
        self.load_model()

    def load_model(self):
        """Load the trained ML model."""
        if not SKLEARN_AVAILABLE:
            return

        try:
            if os.path.exists(self.model_path):
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.vectorizer = data['vectorizer']
                self.feature_names = data.get('feature_names', [])
                logger.info(f"Loaded ML model from {self.model_path}")
            else:
                logger.info("No existing ML model found, will need training")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            self.model = None
            self.vectorizer = None

    def save_model(self):
        """Save the trained ML model."""
        if not SKLEARN_AVAILABLE or not self.model:
            return

        try:
            data = {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'feature_names': self.feature_names,
                'trained_date': datetime.now().isoformat()
            }
            joblib.dump(data, self.model_path)
            logger.info(f"Saved ML model to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving ML model: {e}")

    def extract_file_features(self, file_path: str) -> Dict[str, Any]:
        """Extract features from a file for ML analysis.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary of extracted features
        """
        features = {}

        try:
            if not os.path.exists(file_path):
                return features

            # Basic file properties
            stat = os.stat(file_path)
            features['file_size'] = stat.st_size
            features['is_executable'] = self._is_executable(file_path)

            # File extension
            ext = Path(file_path).suffix.lower()
            features[f'extension_{ext}'] = 1

            # File entropy
            features['entropy'] = self._calculate_entropy(file_path)

            # PE header features (for Windows executables)
            if ext in ['.exe', '.dll', '.sys']:
                pe_features = self._extract_pe_features(file_path)
                features.update(pe_features)

            # String analysis
            string_features = self._extract_string_features(file_path)
            features.update(string_features)

            # Hash features
            file_hash = self._get_file_hash(file_path)
            features['hash_md5'] = int(file_hash[:8], 16) if file_hash else 0
            features['hash_sha256'] = int(file_hash, 16) % (10**8) if file_hash else 0

        except Exception as e:
            logger.error(f"Error extracting features from {file_path}: {e}")

        return features

    def _is_executable(self, file_path: str) -> bool:
        """Check if file is an executable."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                # Check for common executable signatures
                if header.startswith(b'MZ') or header.startswith(b'\x7fELF') or header.startswith(b'\xfe\xed'):
                    return True
        except:
            pass
        return False

    def _calculate_entropy(self, file_path: str, sample_size: int = 1024) -> float:
        """Calculate Shannon entropy of file content."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(sample_size)

            if not data:
                return 0.0

            # Calculate byte frequency
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1

            # Calculate entropy
            entropy = 0.0
            for count in byte_counts:
                if count > 0:
                    p = count / len(data)
                    entropy -= p * (p and p.bit_length() or 0)

            return entropy

        except Exception as e:
            logger.error(f"Error calculating entropy: {e}")
            return 0.0

    def _extract_pe_features(self, file_path: str) -> Dict[str, Any]:
        """Extract features from PE (Portable Executable) headers."""
        features = {}

        try:
            with open(file_path, 'rb') as f:
                # Read DOS header
                dos_header = f.read(64)
                if len(dos_header) < 64 or not dos_header.startswith(b'MZ'):
                    return features

                # Get PE header offset
                pe_offset = struct.unpack('<L', dos_header[60:64])[0]
                f.seek(pe_offset)

                # Read PE signature
                pe_sig = f.read(4)
                if pe_sig != b'PE\x00\x00':
                    return features

                # Read COFF header
                coff_header = f.read(20)
                if len(coff_header) < 20:
                    return features

                machine, number_of_sections, timestamp, symbol_table, number_of_symbols, \
                optional_header_size, characteristics = struct.unpack('<HHLLLHH', coff_header)

                features['pe_machine'] = machine
                features['pe_sections'] = number_of_sections
                features['pe_timestamp'] = timestamp
                features['pe_characteristics'] = characteristics

                # Read optional header if present
                if optional_header_size > 0:
                    optional_header = f.read(min(optional_header_size, 100))
                    if len(optional_header) >= 2:
                        magic = struct.unpack('<H', optional_header[:2])[0]
                        features['pe_magic'] = magic

        except Exception as e:
            logger.error(f"Error extracting PE features: {e}")

        return features

    def _extract_string_features(self, file_path: str) -> Dict[str, Any]:
        """Extract string-based features from file."""
        features = {}

        try:
            suspicious_strings = [
                'malware', 'virus', 'trojan', 'backdoor', 'exploit',
                'cmd.exe', 'powershell', 'regsvr32', 'mshta', 'bitsadmin',
                'certutil', 'rundll32', 'schtasks', 'net user', 'system32'
            ]

            with open(file_path, 'rb') as f:
                content = f.read()

            # Check for suspicious strings
            for string in suspicious_strings:
                if string.encode('utf-8').lower() in content.lower():
                    features[f'string_{string.replace(".", "_")}'] = 1
                else:
                    features[f'string_{string.replace(".", "_")}'] = 0

            # Count total strings
            try:
                text_content = content.decode('utf-8', errors='ignore')
                string_count = len([s for s in text_content.split() if len(s) > 4])
                features['total_strings'] = string_count
            except:
                features['total_strings'] = 0

        except Exception as e:
            logger.error(f"Error extracting string features: {e}")

        return features

    def _get_file_hash(self, file_path: str) -> str:
        """Get MD5 hash of file."""
        try:
            hash_obj = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""

    def predict_threat(self, file_path: str) -> Tuple[float, str]:
        """Predict if a file is a threat using ML model.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Tuple of (confidence_score, threat_category)
        """
        if not self.model or not self.vectorizer:
            return 0.0, "unknown"

        try:
            # Extract features
            features = self.extract_file_features(file_path)

            # Vectorize features
            feature_vector = self.vectorizer.transform([features])

            # Make prediction
            prediction = self.model.predict_proba(feature_vector)[0]

            # Get confidence and category
            max_prob = max(prediction)
            if max_prob > 0.7:  # High confidence threshold
                predicted_class = self.model.classes_[prediction.argmax()]
                return max_prob, predicted_class
            else:
                return 0.0, "unknown"

        except Exception as e:
            logger.error(f"Error making ML prediction: {e}")
            return 0.0, "error"

    def train_model(self, training_data: List[Dict], test_size: float = 0.2) -> Dict:
        """Train the ML model on labeled data.

        Args:
            training_data: List of dictionaries with 'file_path', 'features', and 'label' keys
            test_size: Fraction of data to use for testing

        Returns:
            Dictionary with training results
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not available'}

        try:
            # Prepare training data
            X = []
            y = []

            for sample in training_data:
                features = sample.get('features', {})
                X.append(features)
                y.append(sample.get('label', 'benign'))

            if not X or not y:
                return {'error': 'No training data provided'}

            # Vectorize features
            self.vectorizer = DictVectorizer(sparse=False)
            X_vectorized = self.vectorizer.fit_transform(X)
            self.feature_names = self.vectorizer.feature_names_

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_vectorized, y, test_size=test_size, random_state=42
            )

            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            self.model.fit(X_train, y_train)

            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            self.save_model()

            return {
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': len(self.feature_names),
                'model_classes': list(self.model.classes_)
            }

        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return {'error': str(e)}

    def get_model_info(self) -> Dict:
        """Get information about the current ML model."""
        if not self.model:
            return {'status': 'not_trained'}

        return {
            'status': 'trained',
            'model_type': type(self.model).__name__,
            'feature_count': len(self.feature_names) if self.feature_names else 0,
            'classes': list(self.model.classes_) if hasattr(self.model, 'classes_') else [],
            'model_path': self.model_path
        }


class MLSandboxAnalyzer:
    """Sandbox analysis for suspicious files using ML predictions."""

    def __init__(self):
        """Initialize the ML sandbox analyzer."""
        self.ml_detector = MLThreatDetector()

    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a file using ML-based threat detection.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary with analysis results
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        # Get ML prediction
        confidence, category = self.ml_detector.predict_threat(file_path)

        # Additional analysis
        features = self.ml_detector.extract_file_features(file_path)

        return {
            'file_path': file_path,
            'ml_confidence': confidence,
            'ml_category': category,
            'features_extracted': len(features),
            'file_size': features.get('file_size', 0),
            'entropy': features.get('entropy', 0),
            'is_executable': features.get('is_executable', False),
            'analysis_timestamp': datetime.now().isoformat(),
            'risk_level': self._calculate_risk_level(confidence, category, features)
        }

    def _calculate_risk_level(self, confidence: float, category: str, features: Dict) -> str:
        """Calculate overall risk level based on ML prediction and file features."""
        risk_score = 0

        # ML confidence score
        if confidence > 0.8:
            risk_score += 3
        elif confidence > 0.6:
            risk_score += 2
        elif confidence > 0.4:
            risk_score += 1

        # File characteristics
        if features.get('is_executable', False):
            risk_score += 1

        if features.get('entropy', 0) > 7.0:  # High entropy often indicates packed malware
            risk_score += 2

        if features.get('file_size', 0) > 50 * 1024 * 1024:  # Very large files
            risk_score += 1

        # Category-based risk
        if category in ['malware', 'trojan', 'virus']:
            risk_score += 3
        elif category in ['suspicious']:
            risk_score += 2
        elif category in ['pua']:
            risk_score += 1

        if risk_score >= 6:
            return 'high'
        elif risk_score >= 3:
            return 'medium'
        else:
            return 'low'

    def batch_analyze(self, file_paths: List[str]) -> List[Dict]:
        """Analyze multiple files in batch.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            List of analysis results
        """
        results = []

        for file_path in file_paths:
            try:
                result = self.analyze_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'error': str(e),
                    'analysis_timestamp': datetime.now().isoformat()
                })

        return results

    def generate_ml_report(self, analysis_results: List[Dict]) -> str:
        """Generate a report of ML analysis results.

        Args:
            analysis_results: List of analysis results from batch_analyze

        Returns:
            Formatted report string
        """
        report = []
        report.append("Machine Learning Threat Analysis Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Files Analyzed: {len(analysis_results)}")
        report.append("")

        # Summary statistics
        risk_counts = {'high': 0, 'medium': 0, 'low': 0}
        ml_detections = 0

        for result in analysis_results:
            if 'error' not in result:
                risk_counts[result.get('risk_level', 'low')] += 1
                if result.get('ml_confidence', 0) > 0.5:
                    ml_detections += 1

        report.append("Risk Distribution:")
        for level, count in risk_counts.items():
            percentage = (count / len(analysis_results) * 100) if analysis_results else 0
            report.append(f"  {level.upper()}: {count} files ({percentage:.1f}%)")
        report.append("")

        report.append(f"ML Detections: {ml_detections} files")
        report.append("")

        # Detailed results
        if analysis_results:
            report.append("Detailed Results:")
            report.append("-" * 50)

            for result in analysis_results:
                if 'error' in result:
                    report.append(f"ERROR - {result['file_path']}: {result['error']}")
                else:
                    report.append(f"File: {result['file_path']}")
                    report.append(f"  ML Confidence: {result.get('ml_confidence', 0):.3f}")
                    report.append(f"  ML Category: {result.get('ml_category', 'unknown')}")
                    report.append(f"  Risk Level: {result.get('risk_level', 'unknown')}")
                    report.append(f"  File Size: {result.get('file_size', 0):,} bytes")
                    report.append(f"  Entropy: {result.get('entropy', 0):.2f}")
                    report.append("")

        return "\n".join(report)
