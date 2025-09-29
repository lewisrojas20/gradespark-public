# gradespark_gui.py - Public/Community Version
import sys
import os
import logging
import json
import threading
from datetime import datetime
from pathlib import Path
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QStatusBar, QCheckBox, QLineEdit, QGroupBox, QDialog,
    QFileDialog, QHeaderView, QDesktopWidget, QFrame, QProgressBar, QFormLayout, QGridLayout
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QUrl, QObject, QThread, QStandardPaths, QByteArray
)
from PyQt5.QtGui import QBrush, QColor, QDesktopServices, QIcon

# For lead capture
import urllib.request
import platform

# CRITICAL FIX FOR PYINSTALLER
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str((base_path / relative_path).resolve())

try:
    import resources_rc
except ImportError:
    pass

# --- Background Worker for Demo Grading ---
class Worker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int, str)

    def __init__(self, assignments, subject, grade_level):
        super().__init__()
        self.assignments = assignments
        self.subject = subject
        self.grade_level = grade_level

    def run(self):
        results = self._simulate_grading(self.assignments, self.subject, self.grade_level)
        self.finished.emit(results)
    
    def _simulate_grading(self, assignments, subject, grade_level):
        """Simulate grading for demo mode"""
        import random
        results = []
        total = len(assignments)
        
        for idx, assignment in enumerate(assignments):
            student_name = assignment.get('Student Name', 'Unknown')
            
            # Check if assignment was submitted
            if 'Not submitted' in str(assignment.get('Score', '')):
                results.append({
                    'Student Name': student_name,
                    'Score': 'Not submitted',
                    'Feedback': '',
                    'Rubric': ''
                })
            else:
                # Generate simulated score
                base_score = random.randint(70, 95)
                
                # Generate grade-appropriate feedback
                feedback = self._generate_feedback(base_score, subject, grade_level)
                
                # Generate rubric scores
                rubric = self._generate_rubric(base_score, subject)
                
                results.append({
                    'Student Name': student_name,
                    'Score': str(base_score),
                    'Feedback': feedback,
                    'Rubric': rubric
                })
            
            # Emit progress
            progress_pct = int((idx + 1) / total * 100)
            self.progress.emit(progress_pct, f"Grading {student_name}...")
        
        return results
    
    def _generate_feedback(self, score, subject, grade_level):
        """Generate appropriate feedback based on score and subject"""
        if score >= 90:
            feedback = f"Excellent work! Strong understanding of {subject} concepts at grade {grade_level} level."
        elif score >= 80:
            feedback = f"Good effort! Solid grasp of key {subject} concepts with room for deeper analysis."
        elif score >= 70:
            feedback = f"Satisfactory work. Review core {subject} concepts and practice application."
        else:
            feedback = f"Needs improvement. Schedule extra help to strengthen {subject} fundamentals."
        
        return feedback
    
    def _generate_rubric(self, score, subject):
        """Generate rubric scores based on overall score"""
        if score >= 90:
            return "Content: Excellent | Analysis: Excellent | Presentation: Good"
        elif score >= 80:
            return "Content: Good | Analysis: Good | Presentation: Satisfactory"
        elif score >= 70:
            return "Content: Satisfactory | Analysis: Needs Work | Presentation: Satisfactory"
        else:
            return "Content: Needs Work | Analysis: Needs Work | Presentation: Needs Work"

# --- Settings Management ---
from settings_store import SettingsStore

# --- Demo Data Manager ---
from demo_data_manager import DemoDataManager

# --- Lead Capture Dialog ---
class LeadCaptureDialog(QDialog):
    def __init__(self, parent=None, feature_name="Premium Feature"):
        super().__init__(parent)
        self.feature_name = feature_name
        self.webhook_url = os.environ.get(
            "GRADESPARK_LEAD_WEBHOOK",
            "https://hook.us2.make.com/3tsoiux2mb2pvmd9jh74mf45yfmvljlu"
        )
        self.setWindowTitle(f"{feature_name} - Full Version Only")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        container = QFrame()
        container.setObjectName("leadCaptureContainer")
        container.setMaximumWidth(600)
        container_layout = QVBoxLayout(container)

        is_dark_mode = False
        if hasattr(self.parent(), "settings"):
            is_dark_mode = self.parent().settings.get("dark_mode_enabled", False)

        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setStyleSheet("font-size: 64px;")
        container_layout.addWidget(lock_icon)

        if "Google Classroom" in self.feature_name:
            title_text = "Google Classroom Integration"
            subtitle_text = "Full Version Only"
        else:
            title_text = self.feature_name
            subtitle_text = "Full Version Only"

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e66ff;")
        container_layout.addWidget(title)

        subtitle = QLabel(subtitle_text)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; font-weight: 600; color: #666;")
        container_layout.addWidget(subtitle)

        desc = QLabel(
            "This feature is available in the full version of GradeSpark.\n"
            "Be among the first teachers to revolutionize your grading workflow!"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "font-size: 16px; "
            + ("color: #B0B0B0; margin: 20px 0;" if is_dark_mode else "color: #666; margin: 20px 0;")
        )
        container_layout.addWidget(desc)

        if is_dark_mode:
            container.setStyleSheet(
                """
                QFrame#leadCaptureContainer {
                    background-color: rgba(40, 40, 45, 0.95);
                    border-radius: 12px;
                    padding: 40px;
                }
                QFrame#leadCaptureContainer QLabel {
                    color: #E0E0E0;
                }
                QLineEdit, QComboBox {
                    background-color: #2C2C30;
                    color: #E0E0E0;
                    border: 1px solid #444;
                    padding: 8px;
                    border-radius: 4px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border: 1px solid #1e66ff;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: url(:/assets/chevron-down-dark.svg);
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2C2C30;
                    color: #E0E0E0;
                    selection-background-color: #1e66ff;
                    selection-color: white;
                    border: 1px solid #444;
                }
            """
            )
        else:
            container.setStyleSheet(
                """
                QFrame#leadCaptureContainer {
                    background-color: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    padding: 40px;
                }
                QLineEdit, QComboBox {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #DDD;
                    padding: 8px;
                    border-radius: 4px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border: 1px solid #1e66ff;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: url(:/assets/chevron-down.svg);
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #333333;
                    selection-background-color: #1e66ff;
                    selection-color: white;
                    border: 1px solid #DDD;
                }
            """
            )

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(15)

        label_style = "color: #666;" if not is_dark_mode else "color: #999;"

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("John Doe")
        name_label = QLabel("Name:")
        name_label.setStyleSheet(label_style)
        form_layout.addRow(name_label, self.name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("teacher@school.edu")
        email_label = QLabel("Email:")
        email_label.setStyleSheet(label_style)
        form_layout.addRow(email_label, self.email_input)

        self.school_input = QLineEdit()
        self.school_input.setPlaceholderText("Lincoln Middle School")
        school_label = QLabel("School/District:")
        school_label.setStyleSheet(label_style)
        form_layout.addRow(school_label, self.school_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["I'm a Teacher", "I'm a School Administrator"])
        role_label = QLabel("Role:")
        role_label.setStyleSheet(label_style)
        form_layout.addRow(role_label, self.role_combo)

        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Just me (1 teacher)",
            "Small team (2-5 teachers)",
            "Department (6-20 teachers)",
            "School-wide (20+ teachers)"
        ])
        size_label = QLabel("Team Size:")
        size_label.setStyleSheet(label_style)
        form_layout.addRow(size_label, self.size_combo)

        self.timeline_combo = QComboBox()
        self.timeline_combo.addItems([
            "Ready now",
            "This semester",
            "Next school year",
            "Just exploring"
        ])
        timeline_label = QLabel("Timeline:")
        timeline_label.setStyleSheet(label_style)
        form_layout.addRow(timeline_label, self.timeline_combo)

        container_layout.addWidget(form_widget)

        self.submit_btn = QPushButton("Get Early Access")
        self.submit_btn.setObjectName("primaryButton")
        self.submit_btn.clicked.connect(self.submit_lead)
        container_layout.addWidget(self.submit_btn)

        privacy = QLabel("We'll only use your email to send you updates about GradeSpark.")
        privacy.setAlignment(Qt.AlignCenter)
        privacy.setStyleSheet(
            "font-size: 12px; "
            + ("color: #888; margin-top: 10px;" if is_dark_mode else "color: #999; margin-top: 10px;")
        )
        container_layout.addWidget(privacy)

        layout.addWidget(container)

    def submit_lead(self):
        """Validate input, queue background send, and thank the user"""
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        school = self.school_input.text().strip()

        if not name or not email or not school:
            QMessageBox.warning(
                self,
                "Incomplete Form",
                "Please fill in all required fields (Name, Email, School)"
            )
            return

        lead_payload = {
            "name": name,
            "email": email,
            "school": school,
            "role": self.role_combo.currentText(),
            "size": self.size_combo.currentText(),
            "timeline": self.timeline_combo.currentText(),
            "feature": self.feature_name,
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system()
        }

        self.send_to_webhook(lead_payload)
        self._reset_form()

        QMessageBox.information(
            self,
            "Thanks!",
            f"Thanks {name}! We'll be in touch soon about early access to {self.feature_name}."
        )
        self.accept()

    def _reset_form(self):
        self.name_input.clear()
        self.email_input.clear()
        self.school_input.clear()
        self.role_combo.setCurrentIndex(0)
        self.size_combo.setCurrentIndex(0)
        self.timeline_combo.setCurrentIndex(0)

    def send_to_webhook(self, payload):
        """Send lead data asynchronously"""

        def _post_lead(data):
            try:
                json_bytes = json.dumps(data).encode("utf-8")
                request = urllib.request.Request(
                    self.webhook_url,
                    data=json_bytes,
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(request, timeout=5) as response:
                    if 200 <= response.status < 300:
                        logging.info("Lead sent successfully: %s", data.get("email"))
                        return
                    logging.warning(
                        "Lead webhook returned status %s for %s",
                        response.status,
                        data.get("email")
                    )
            except Exception as exc:  # noqa: BLE001 - log and fall back
                logging.debug("Lead webhook failed: %s", exc)
            self.save_lead_locally(data)

        threading.Thread(target=_post_lead, args=(payload,), daemon=True).start()

    def save_lead_locally(self, lead_data):
        """Persist lead details in the user's application data folder."""
        try:
            target_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if not target_dir:
                target_dir = str(Path.home() / ".gradespark")

            storage_path = Path(target_dir)
            storage_path.mkdir(parents=True, exist_ok=True)

            leads_file = storage_path / "leads_backup.json"
            existing_leads = []

            if leads_file.exists():
                try:
                    with leads_file.open("r", encoding="utf-8") as handle:
                        existing_leads = json.load(handle)
                except json.JSONDecodeError:
                    logging.warning("Failed to decode existing lead backup; starting fresh.")

            existing_leads.append(lead_data)

            with leads_file.open("w", encoding="utf-8") as handle:
                json.dump(existing_leads, handle, indent=2)

            logging.info("Lead saved locally: %s", lead_data.get("email"))
        except Exception as exc:  # noqa: BLE001 - capture unexpected filesystem issues
            logging.error("Failed to save lead locally: %s", exc)


class GuidedTourDialog(QDialog):
    """Simple guided tour to orient new community-edition users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to GradeSpark")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.steps = [
            (
                "Explore Demo Mode",
                "Start on the Home tab, then tap Try Demo Mode to experience a full grading workflow with sample data."
            ),
            (
                "Review Results",
                "Once the simulation finishes, open the Results Viewer to inspect AI-style feedback and export a CSV."
            ),
            (
                "Unlock Premium Workflows",
                "Classroom Mode and Live Grading stay locked here - click them anytime to request early access to the full platform."
            )
        ]
        self.current_index = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.heading_label = QLabel()
        self.heading_label.setAlignment(Qt.AlignCenter)
        self.heading_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.heading_label)

        self.body_label = QLabel()
        self.body_label.setWordWrap(True)
        self.body_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.body_label.setStyleSheet("font-size: 15px; line-height: 1.5;")
        layout.addWidget(self.body_label)

        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #666; margin-top: 12px;")
        layout.addWidget(self.progress_label)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.skip_button = QPushButton("Skip Tour")
        self.skip_button.clicked.connect(self.reject)
        button_row.addWidget(self.skip_button)

        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("primaryButton")
        self.next_button.clicked.connect(self.advance)
        button_row.addWidget(self.next_button)

        layout.addLayout(button_row)
        self.refresh_content()

    def refresh_content(self):
        title, body = self.steps[self.current_index]
        self.heading_label.setText(title)
        self.body_label.setText(body)
        self.progress_label.setText(
            f"Step {self.current_index + 1} of {len(self.steps)}"
        )
        if self.current_index == len(self.steps) - 1:
            self.next_button.setText("Finish")
        else:
            self.next_button.setText("Next")

    def advance(self):
        if self.current_index == len(self.steps) - 1:
            self.accept()
            return
        self.current_index += 1
        self.refresh_content()

# --- Main GUI Application ---
class GradeSparkGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize settings manager
        self.settings = SettingsStore()
        
        # Initialize demo data manager - FIX PATH HERE
        self.demo_manager = DemoDataManager(data_dir=resource_path("demo_data"))
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize UI
        self.init_ui()
        
        # Apply saved settings
        self.apply_saved_settings()
        
        # Restore window geometry
        self.restore_window_geometry()
        
        # Initialize variables
        self.current_results = None
        QTimer.singleShot(600, self.maybe_start_guided_tour)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("GradeSpark - AI Grading Assistant (Community Edition)")
        
        # Set window size
        self.resize(1200, 800)
        self.center_window()
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_home_tab()
        self.create_demo_mode_tab()
        self.create_classroom_mode_tab()
        self.create_live_grading_tab()
        self.create_results_viewer_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Community Edition")
        
        # Apply theme
        self.apply_theme()
    
    def create_home_tab(self):
        """Create the Home/Welcome tab"""
        home_widget = QWidget()
        layout = QVBoxLayout(home_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(32)
        layout.setContentsMargins(80, 120, 80, 100)

        # Welcome section
        welcome_label = QLabel("Welcome to GradeSpark")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setObjectName("heroTitle")
        layout.addWidget(welcome_label)
        
        subtitle = QLabel("Experience AI-Powered Grading with Demo Mode!")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("heroSubtitle")
        layout.addWidget(subtitle)
        
        layout.addSpacing(24)

        features_layout = QVBoxLayout()
        features_layout.setSpacing(10)

        features = [
            "📚 Full Demo Mode with 24 realistic datasets",
            "📝 Experience the complete grading workflow",
            "📊 See AI-generated feedback in action",
            "💡 Export results and share with colleagues",
            "🚀 Unlock pro features for live grading"
        ]

        for feature in features:
            label = QLabel(feature)
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("featureLabel")
            features_layout.addWidget(label)

        features_container = QWidget()
        features_container.setLayout(features_layout)
        layout.addWidget(features_container)

        layout.addSpacing(40)

        # CTA buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setAlignment(Qt.AlignCenter)
        
        demo_btn = QPushButton("Try Demo Mode")
        demo_btn.setObjectName("primaryButton")
        demo_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        button_layout.addWidget(demo_btn)
        
        full_version_btn = QPushButton("Get Full Version")
        full_version_btn.setObjectName("secondaryButton")
        full_version_btn.clicked.connect(self.show_full_version_info)
        button_layout.addWidget(full_version_btn)
        
        layout.addLayout(button_layout)

        self.tabs.addTab(home_widget, "Home")
        self.update_theme_dependent_styles()
    
    def create_demo_mode_tab(self):
        """Create the Demo Mode tab"""
        demo_widget = QWidget()
        layout = QVBoxLayout(demo_widget)
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(32)
        
        # Header
        header = QLabel("Experience GradeSpark with realistic sample data - no setup required")
        header.setAlignment(Qt.AlignLeft)
        header.setObjectName("demoHeader")
        layout.addWidget(header)

        controls_widget = QWidget()
        controls_layout = QGridLayout(controls_widget)
        controls_layout.setHorizontalSpacing(32)
        controls_layout.setVerticalSpacing(18)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        grade_label = QLabel("Grade Level")
        self.grade_combo = QComboBox()
        self.grade_combo.setMinimumWidth(160)
        controls_layout.addWidget(grade_label, 0, 0)
        controls_layout.addWidget(self.grade_combo, 0, 1)

        subject_label = QLabel("Subject")
        self.subject_combo = QComboBox()
        controls_layout.addWidget(subject_label, 0, 2)
        controls_layout.addWidget(self.subject_combo, 0, 3)

        assignment_label = QLabel("Assignment")
        self.assignment_combo = QComboBox()
        controls_layout.addWidget(assignment_label, 0, 4)
        controls_layout.addWidget(self.assignment_combo, 0, 5)

        controls_layout.setColumnStretch(1, 1)
        controls_layout.setColumnStretch(3, 1)
        controls_layout.setColumnStretch(5, 1)

        layout.addWidget(controls_widget)

        # Update dropdowns when selections change
        self.grade_combo.currentTextChanged.connect(self.update_subject_list)
        self.subject_combo.currentTextChanged.connect(self.update_assignment_list)

        # Run button
        run_btn = QPushButton("Run Demo Mode")
        run_btn.setObjectName("primaryButton")
        run_btn.clicked.connect(self.run_demo_mode)
        layout.addWidget(run_btn)
        
        # Info button
        info_btn = QPushButton("How does it work?")
        info_btn.setObjectName("linkButton")
        info_btn.clicked.connect(self.show_demo_info)
        layout.addWidget(info_btn)
        
        # Progress bar
        self.demo_progress = QProgressBar()
        self.demo_progress.setVisible(False)
        layout.addWidget(self.demo_progress)

        # Add stretch
        layout.addStretch()
        self.populate_demo_selectors()

        self.tabs.addTab(demo_widget, "Demo Mode")
        self.update_theme_dependent_styles()
    
    def create_classroom_mode_tab(self):
        """Create the Classroom Mode tab - shows lead capture"""
        classroom_widget = QWidget()
        layout = QVBoxLayout(classroom_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setObjectName("lockIcon")
        layout.addWidget(lock_icon)

        title = QLabel("Google Classroom Integration")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("lockedTitle")
        layout.addWidget(title)

        description = QLabel("Import assignments and rosters directly from Google Classroom to jump-start AI grading.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setObjectName("lockedDescription")
        layout.addWidget(description)

        layout.addSpacing(12)

        connect_btn = QPushButton("Request Access to the Full Version")
        connect_btn.setObjectName("primaryButton")
        connect_btn.clicked.connect(lambda: self.show_lead_capture("Google Classroom Integration"))
        layout.addWidget(connect_btn)

        learn_more_btn = QPushButton("How does it work?")
        learn_more_btn.setObjectName("linkButton")
        learn_more_btn.clicked.connect(self.show_classroom_info)
        layout.addWidget(learn_more_btn)

        layout.addStretch()

        self.tabs.addTab(classroom_widget, "Classroom Mode")

    def create_live_grading_tab(self):
        """Create the Live Grading tab - shows lead capture"""
        live_widget = QWidget()
        layout = QVBoxLayout(live_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setObjectName("lockIcon")
        layout.addWidget(lock_icon)

        title = QLabel("Live AI Grading")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("lockedTitle")
        layout.addWidget(title)

        description = QLabel("Upload essays and assessments for instant AI scoring, feedback, and rubric alignment.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setObjectName("lockedDescription")
        layout.addWidget(description)

        layout.addSpacing(12)

        upload_btn = QPushButton("Request Access to the Full Version")
        upload_btn.setObjectName("primaryButton")
        upload_btn.clicked.connect(lambda: self.show_lead_capture("Live AI Grading"))
        layout.addWidget(upload_btn)

        live_info_btn = QPushButton("How does it work?")
        live_info_btn.setObjectName("linkButton")
        live_info_btn.clicked.connect(self.show_live_grading_info)
        layout.addWidget(live_info_btn)

        layout.addStretch()

        self.tabs.addTab(live_widget, "Live Grading")
    
    def create_results_viewer_tab(self):
        """Create the Results Viewer tab"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)
        layout.setContentsMargins(40, 40, 40, 50)
        layout.setSpacing(20)

        # Export buttons
        button_layout = QHBoxLayout()

        export_csv_btn = QPushButton("Export to CSV")
        export_csv_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(export_csv_btn)
        
        clear_btn = QPushButton("Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Student Name", "Score", "Feedback", "Rubric"])
        self.results_table.setAlternatingRowColors(False)

        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.results_table.setColumnWidth(1, 80)

        layout.addWidget(self.results_table)
        self.results_table.cellDoubleClicked.connect(self.show_feedback_spotlight)

        legend_bar = self._build_results_legend()
        layout.addWidget(legend_bar)

        self.tabs.addTab(results_widget, "Results Viewer")

    def create_settings_tab(self):
        """Create the Settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setAlignment(Qt.AlignTop)
        
        # Display Options group
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout()
        
        self.rubric_checkbox = QCheckBox("Show rubric categories")
        self.rubric_checkbox.setChecked(self.settings.get("show_rubric", True))
        self.rubric_checkbox.stateChanged.connect(self.save_settings)
        display_layout.addWidget(self.rubric_checkbox)
        
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.settings.get("dark_mode_enabled", False))
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        display_layout.addWidget(self.dark_mode_checkbox)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Advanced group
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QVBoxLayout()
        
        logs_btn = QPushButton("Open Logs Folder")
        logs_btn.clicked.connect(self.open_logs_folder)
        advanced_layout.addWidget(logs_btn)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Note about Community Edition
        note_label = QLabel("Note: This is the Community Edition. API configuration and Google Classroom features are available in the full version.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #888; font-style: italic; margin-top: 20px;")
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        self.tabs.addTab(settings_widget, "Settings")
    
    # --- Demo Mode Methods ---
    def populate_demo_selectors(self):
        """Initialise grade, subject, and assignment dropdowns from demo data."""
        grades = self.demo_manager.get_grades()
        self.grade_combo.blockSignals(True)
        self.grade_combo.clear()
        self.grade_combo.addItems(grades)
        self.grade_combo.blockSignals(False)

        if grades:
            self.grade_combo.setCurrentIndex(0)
            self.update_subject_list()
        else:
            self.subject_combo.clear()
            self.assignment_combo.clear()

    def update_subject_list(self):
        """Populate subject dropdown based on selected grade."""
        grade = self.grade_combo.currentText()
        subjects = self.demo_manager.get_subjects(grade)

        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        self.subject_combo.addItems(subjects)
        self.subject_combo.blockSignals(False)

        if subjects:
            self.subject_combo.setCurrentIndex(0)
        else:
            self.assignment_combo.clear()

        self.update_assignment_list()

    def update_assignment_list(self):
        """Update assignment dropdown based on selected grade and subject."""
        grade = self.grade_combo.currentText()
        subject = self.subject_combo.currentText()
        assignments = self.demo_manager.get_assignments(grade, subject)

        self.assignment_combo.blockSignals(True)
        self.assignment_combo.clear()
        self.assignment_combo.addItems(assignments)
        self.assignment_combo.blockSignals(False)

        if assignments:
            self.assignment_combo.setCurrentIndex(0)

    def run_demo_mode(self):
        """Run the demo mode grading simulation"""
        grade = self.grade_combo.currentText()
        subject = self.subject_combo.currentText()
        assignment = self.assignment_combo.currentText()
        
        # Check if demo data exists
        if not self.demo_manager.check_data_exists():
            QMessageBox.critical(self, "Demo Data Missing",
                "Demo data files are missing. Please ensure the demo_data folder is in the application directory.")
            return
        
        # Load demo data
        df, submitted, total, missing = self.demo_manager.load_csv(grade, subject, assignment)
        if df is None:
            QMessageBox.warning(self, "No Data",
                f"No demo data available for Grade {grade} {subject} - {assignment}")
            return

        try:
            # Load the CSV data
            assignments = df.to_dict('records')
            
            # Setup progress
            self.demo_progress.setVisible(True)
            self.demo_progress.setValue(0)
            self.status_bar.showMessage(
                f"Running Demo Mode: Grade {grade} {subject} - {assignment} "
                f"({submitted} of {total} submissions, {missing} missing)"
            )
            
            # Create worker thread
            self.thread = QThread()
            self.worker = Worker(assignments, subject, grade)
            self.worker.moveToThread(self.thread)
            
            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.update_demo_progress)
            self.worker.finished.connect(self.demo_grading_complete)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            
            # Start grading
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load demo data: {str(e)}")
    
    def update_demo_progress(self, value, message):
        """Update progress bar during demo grading"""
        self.demo_progress.setValue(value)
        self.status_bar.showMessage(message)
    
    def demo_grading_complete(self, results):
        """Handle completion of demo grading"""
        self.demo_progress.setVisible(False)
        self.current_results = results

        # Populate results table
        self.populate_results_table(results)
        self.status_bar.showMessage(
            f"Demo grading complete - {len(results)} assignments processed"
        )

        submitted = sum(1 for r in results if r['Score'] != 'Not submitted')
        missing = len(results) - submitted
        missing_names = [r['Student Name'] for r in results if r['Score'] == 'Not submitted']

        summary_lines = [
            f"Assignments graded: {submitted}",
            f"Awaiting submission: {missing}",
        ]
        if missing_names:
            preview = ", ".join(missing_names[:5])
            if len(missing_names) > 5:
                preview += ", ..."
            summary_lines.append(f"Missing students: {preview}")

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Demo Complete")
        msg_box.setText("Demo grading finished successfully.")
        msg_box.setInformativeText("\n".join(summary_lines))
        view_button = msg_box.addButton("View Results", QMessageBox.AcceptRole)
        msg_box.addButton("Stay on Demo Tab", QMessageBox.RejectRole)
        msg_box.exec_()

        if msg_box.clickedButton() is view_button:
            self.tabs.setCurrentIndex(4)
    
    def show_demo_info(self):
        """Show information about demo mode"""
        bullets = [
            "24 different datasets (3 grades × 4 subjects × 2 assignments).",
            "Realistic student submissions with varied scores.",
            "AI-style feedback generation.",
            "Export results to CSV.",
            "All offline – no API keys or real student data required.",
        ]
        self.show_info_dialog("Demo Mode Simulates the Full Workflow", bullets)

    def show_info_dialog(self, title, bullet_points):
        """Show a formatted informational dialog with bullet points."""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setWindowTitle(title)
        dialog.setText(f"<b>{title}</b>")
        bullets = "<br>".join(f"• {point}" for point in bullet_points)
        dialog.setInformativeText(bullets)
        dialog.exec_()

    def show_classroom_info(self):
        bullets = [
            "Seamlessly import your class rosters and assignments.",
            "Pull student submissions (PDFs, Docs) with a single click.",
            "Grade entire classes in minutes, not hours.",
            "Return grades and AI-powered feedback directly to students (coming in Pro).",
            "Request access to be the first to try the full version!",
        ]
        self.show_info_dialog("Automate Your Workflow with Google Classroom", bullets)

    def show_live_grading_info(self):
        bullets = [
            "Drag and drop any student work (PDF, DOCX, TXT) from your computer.",
            "Our AI engine provides a score, rubric breakdown, and specific feedback.",
            "Perfect for grading files from any source, not just Google Classroom.",
            "The fastest way to see the power of GradeSpark on your own assignments.",
            "Request access to unlock this powerful feature!",
        ]
        self.show_info_dialog("Grade Any File, Instantly", bullets)
    
    # --- Lead Capture Methods ---
    def show_lead_capture(self, feature_name):
        """Show lead capture dialog for premium features"""
        dialog = LeadCaptureDialog(self, feature_name)
        dialog.exec_()
    
    def show_full_version_info(self):
        """Show information about the full version"""
        dialog = LeadCaptureDialog(self, "Full Version Features")
        dialog.exec_()
    
    # --- Results Methods ---
    def populate_results_table(self, results):
        """Populate the results table with grading data"""
        self.results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            # Student Name
            self.results_table.setItem(row, 0, QTableWidgetItem(result['Student Name']))

            # Score
            score_item = QTableWidgetItem(str(result['Score']))
            self.results_table.setItem(row, 1, score_item)
            score_item.setForeground(QBrush(self._score_bucket_color(result['Score'])))

            # Feedback
            self.results_table.setItem(row, 2, QTableWidgetItem(result['Feedback']))

            # Rubric
            if self.settings.get("show_rubric", True):
                self.results_table.setItem(row, 3, QTableWidgetItem(result['Rubric']))
            else:
                self.results_table.setItem(row, 3, QTableWidgetItem(""))

            self._apply_score_styling(row, result['Score'])

    def show_feedback_spotlight(self, row, _column):
        """Display a focused view of the student's feedback with an upgrade CTA."""
        if not self.current_results or row >= len(self.current_results):
            return

        result = self.current_results[row]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Feedback Spotlight - {result['Student Name']}")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)

        dialog_layout = QVBoxLayout(dialog)

        score_label = QLabel(f"Score: {result['Score']}")
        score_label.setStyleSheet("font-weight: 600; font-size: 16px;")
        dialog_layout.addWidget(score_label)

        feedback_label = QLabel(result.get('Feedback', ''))
        feedback_label.setWordWrap(True)
        feedback_label.setStyleSheet("line-height: 1.6; margin-top: 10px;")
        dialog_layout.addWidget(feedback_label)

        if self.settings.get("show_rubric", True):
            rubric_label = QLabel(result.get('Rubric', ''))
            rubric_label.setWordWrap(True)
            rubric_label.setStyleSheet("color: #555; margin-top: 10px;")
            dialog_layout.addWidget(rubric_label)

        cta_button = QPushButton("Unlock Live Grading")
        cta_button.setObjectName("primaryButton")

        def _launch_upgrade():
            dialog.accept()
            self.show_lead_capture("Live AI Grading")

        cta_button.clicked.connect(_launch_upgrade)
        dialog_layout.addWidget(cta_button)

        dialog.exec_()

    def _apply_score_styling(self, row_index, score_value):
        """Apply subtle row tinting based on score bucket."""
        palette = {
            "missing": "#ef4444",
            "failing": "#ef4444",
            "needs_improvement": "#facc15",
            "understanding": "#4ade80",
            "proficient": "#16a34a",
        }

        category = "missing"
        numeric_score = None
        try:
            numeric_score = float(score_value)
        except (TypeError, ValueError):
            pass

        if numeric_score is not None:
            if numeric_score <= 65:
                category = "failing"
            elif numeric_score <= 75:
                category = "needs_improvement"
            elif numeric_score <= 89:
                category = "understanding"
            else:
                category = "proficient"

        for column in range(self.results_table.columnCount()):
            item = self.results_table.item(row_index, column)
            if not item:
                continue
            item.setBackground(QBrush(Qt.transparent))

    def _score_bucket_color(self, score_value):
        """Return a text color for the score column based on bucket."""
        try:
            numeric_score = float(score_value)
        except (TypeError, ValueError):
            return QColor("#b91c1c")  # treat non-submitters as failing

        if numeric_score <= 65:
            return QColor("#b91c1c")  # red
        if numeric_score <= 75:
            return QColor("#ca8a04")  # yellow
        if numeric_score <= 89:
            return QColor("#15803d")  # green
        return QColor("#1d4ed8")  # blue for top performers

    def _build_results_legend(self):
        """Create the color legend for score buckets."""
        legend_frame = QFrame()
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(0, 12, 0, 0)
        legend_layout.setSpacing(18)

        entries = [
            ("#ef4444", "Red = Failed/Not Submitted"),
            ("#facc15", "Yellow = Needs Extra Support"),
            ("#16a34a", "Green = Proficient"),
            ("#2563eb", "Blue = Exceptional Performance"),
        ]

        for color, text in entries:
            label = QLabel(f"<span style='color:{color}; font-weight:700;'>•</span> {text}")
            legend_layout.addWidget(label)

        legend_layout.addStretch()
        return legend_frame

    def export_to_csv(self):
        """Export results to CSV file"""
        if not self.current_results:
            QMessageBox.warning(self, "No Results", "No results to export. Run Demo Mode first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                df = pd.DataFrame(self.current_results)
                df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def clear_results(self):
        """Clear the results table"""
        self.results_table.setRowCount(0)
        self.current_results = None
        self.status_bar.showMessage("Results cleared")
    
    # --- Settings Methods ---
    def save_settings(self):
        """Save current settings"""
        self.settings["show_rubric"] = self.rubric_checkbox.isChecked()
        self.settings.save()
    
    def toggle_dark_mode(self):
        """Toggle dark mode theme"""
        self.settings["dark_mode_enabled"] = self.dark_mode_checkbox.isChecked()
        self.settings.save()
        self.apply_theme()
        QApplication.processEvents()  # Force UI refresh
    
    def apply_theme(self):
        """Apply the selected theme"""
        if self.settings.get("dark_mode_enabled", False):
            # Apply dark theme - FIX PATH HERE
            try:
                with open(resource_path("styles_dark.qss"), "r") as f:
                    self.setStyleSheet(f.read())
            except:
                # Fallback if file not found
                self.setStyleSheet("")
        else:
            # Apply light theme - FIX PATH HERE
            try:
                with open(resource_path("styles.qss"), "r") as f:
                    self.setStyleSheet(f.read())
            except:
                # Fallback if file not found
                self.setStyleSheet("")

        self.update_theme_dependent_styles()

    def open_logs_folder(self):
        """Open the logs folder"""
        logs_path = Path(resource_path("logs"))
        logs_path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_path)))
    
    # --- Window Management ---
    def center_window(self):
        """Center the window on screen"""
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def apply_saved_settings(self):
        """Apply saved settings on startup"""
        # Apply theme
        if self.settings.get("dark_mode_enabled", False):
            self.dark_mode_checkbox.setChecked(True)
            self.apply_theme()
        
        # Apply other settings
        if not self.settings.get("show_rubric", True):
            self.rubric_checkbox.setChecked(False)

    def maybe_start_guided_tour(self):
        """Show the guided tour on first launch of the community edition."""
        if self.settings.get("tour_completed", False):
            return

        tour_dialog = GuidedTourDialog(self)
        tour_dialog.exec_()
        self.settings["tour_completed"] = True
        self.settings.save()

    def restore_window_geometry(self):
        """Restore window size and position"""
        geometry = self.settings.get("window_geometry")
        if geometry:
            byte_array = QByteArray.fromBase64(geometry.encode("utf-8"))
            if not byte_array.isEmpty():
                self.restoreGeometry(byte_array)

    def closeEvent(self, event):
        """Save settings before closing"""
        # Save window geometry
        geometry_bytes = self.saveGeometry().toBase64().data().decode("utf-8")
        self.settings["window_geometry"] = geometry_bytes
        self.settings.save()
        event.accept()

    def update_theme_dependent_styles(self):
        """Inline overrides no longer required; styling handled via QSS."""
        return

# --- Application Entry Point ---
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GradeSpark Community")
    app.setOrganizationName("GradeSpark")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = GradeSparkGUI()

    icon_path = resource_path("assets/gradespark.ico")
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
        window.setWindowIcon(icon)

    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
