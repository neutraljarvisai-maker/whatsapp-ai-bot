# Vision Architecture Report

## 1. Vision Abstraction
VECTA now features a modular vision architecture that separates screenshot analysis from planning logic.

- **Base Interface**: `core/vision/base.py` defines `BaseVision`.
- **Primary Provider**: `GeminiVision` (`core/vision/gemini.py`) implements cloud-based screenshot analysis.
- **Factory Pattern**: `core/vision/factory.py` allows runtime switching of vision providers via the `VECTA_VISION_PROVIDER` environment variable.

## 2. Request Pipeline
The vision pipeline is integrated into `JarvisBrain.analyze_screen_and_plan`:

1.  **Capture**: (Client-side) Takes a screenshot of the desktop.
2.  **Upload**: Screenshot is sent to the backend `/plan_action` endpoint.
3.  **Analysis**: `brain.analyze_screen_and_plan` calls the selected vision provider.
4.  **Prompting**: The provider is prompted with the current task and previous action history.
5.  **Action**: Provider returns a structured action (e.g., `CLICK(x, y)`).

## 3. Future Readiness
The architecture is designed to support local vision models (e.g., LLaVA, Moondream) as they become available via Ollama or other local inference engines. A new provider can be added by implementing the `BaseVision` interface and registering it in the factory.
