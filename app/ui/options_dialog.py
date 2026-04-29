from __future__ import annotations

from pathlib import Path
from threading import Thread

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.transcription import TranscriptionService
from app.utils.logger import get_logger

AUDIO_FILE_FILTER = (
    "Audio files (*.wav *.mp3 *.m4a *.flac *.ogg *.aac *.wma *.opus *.webm *.mp4 *.mkv)"
)
ALLOWED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
    ".aac",
    ".wma",
    ".opus",
    ".webm",
    ".mp4",
    ".mkv",
}


def resolve_output_txt_path(output_value: str | Path, audio_path: str | Path) -> Path:
    output_text = str(output_value).strip()
    output = Path(output_text)
    audio = Path(audio_path)
    treat_as_directory = False

    if output_text.endswith(("/", "\\")):
        treat_as_directory = True
    elif output.exists() and output.is_dir():
        treat_as_directory = True
    elif output.suffix == "":
        treat_as_directory = True

    if treat_as_directory:
        return output / f"{audio.stem}.txt"
    if output.suffix.lower() != ".txt":
        return output.with_suffix(".txt")
    return output


class _ProcessingBridge(QObject):
    finished = Signal(bool, str)


class ProcessingStatusDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        root = QVBoxLayout(self)
        self._label = QLabel("Processing...", self)
        root.addWidget(self._label)

        self._ok_button = QPushButton("Ok", self)
        self._ok_button.hide()
        self._ok_button.clicked.connect(self.accept)
        root.addWidget(self._ok_button)

    def mark_done(self) -> None:
        self._label.setText("Done")
        self._ok_button.show()


class OptionsDialog(QDialog):
    def __init__(self, transcriber: TranscriptionService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = get_logger(__name__)
        self._transcriber = transcriber
        self._bridge = _ProcessingBridge()
        self._bridge.finished.connect(self._on_processing_finished)
        self._status_dialog: ProcessingStatusDialog | None = None

        self.setWindowTitle("Options")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        root = QVBoxLayout(self)
        form = QFormLayout()

        output_row = QHBoxLayout()
        self._output_path_input = QLineEdit(self)
        self._output_path_input.setPlaceholderText("Output .txt path or folder")
        output_row.addWidget(self._output_path_input)
        output_browse_button = QPushButton("Browse", self)
        output_browse_button.clicked.connect(self._choose_output_path)
        output_row.addWidget(output_browse_button)
        output_row_widget = QWidget(self)
        output_row_widget.setLayout(output_row)
        form.addRow("Output path", output_row_widget)

        audio_row = QHBoxLayout()
        self._audio_path_input = QLineEdit(self)
        self._audio_path_input.setPlaceholderText("Audio file path")
        audio_row.addWidget(self._audio_path_input)
        audio_browse_button = QPushButton("Browse", self)
        audio_browse_button.clicked.connect(self._choose_audio_file)
        audio_row.addWidget(audio_browse_button)
        audio_row_widget = QWidget(self)
        audio_row_widget.setLayout(audio_row)
        form.addRow("Audio file", audio_row_widget)

        root.addLayout(form)
        self._process_button = QPushButton("Process", self)
        self._process_button.clicked.connect(self._start_processing)
        root.addWidget(self._process_button)

    def _choose_output_path(self) -> None:
        selected, _filter = QFileDialog.getSaveFileName(
            self,
            "Choose output txt file",
            "",
            "Text files (*.txt);;All files (*)",
        )
        if selected:
            self._output_path_input.setText(selected)

    def _choose_audio_file(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Choose audio file",
            "",
            AUDIO_FILE_FILTER,
        )
        if selected:
            self._audio_path_input.setText(selected)

    def _start_processing(self) -> None:
        audio_path = Path(self._audio_path_input.text().strip())
        output_value = self._output_path_input.text().strip()
        if not output_value:
            self._show_error("Output path is required.")
            return
        if not audio_path.is_file():
            self._show_error("Audio file does not exist.")
            return
        if audio_path.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
            self._show_error("Only valid audio files are allowed.")
            return

        try:
            output_path = resolve_output_txt_path(output_value, audio_path)
        except Exception:
            self._show_error("Invalid output path.")
            return

        self._process_button.setEnabled(False)
        self._status_dialog = ProcessingStatusDialog(self)
        self._status_dialog.show()
        self._status_dialog.raise_()
        self._status_dialog.activateWindow()
        Thread(
            target=self._process_file,
            args=(audio_path, output_path),
            daemon=True,
        ).start()

    def _process_file(self, audio_path: Path, output_path: Path) -> None:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result = self._transcriber.transcribe_file(audio_path)
            output_path.write_text(result.text, encoding="utf-8")
            self._bridge.finished.emit(True, "")
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Failed processing audio file")
            self._bridge.finished.emit(False, str(exc))

    def _on_processing_finished(self, success: bool, error_message: str) -> None:
        self._process_button.setEnabled(True)
        if self._status_dialog is None:
            return
        if success:
            self._status_dialog.mark_done()
        else:
            self._status_dialog.close()
            self._status_dialog = None
            self._show_error(f"Failed to process file: {error_message}")

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Options", message)
