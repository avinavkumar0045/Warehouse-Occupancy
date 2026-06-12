import cv2
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RTSPService:
    """
    Service to handle connections, frame captures, and disconnections for RTSP camera streams.
    """

    def __init__(self) -> None:
        self.cap: Optional[cv2.VideoCapture] = None
        self.rtsp_url: Optional[str] = None
        self.is_mock: bool = False

    def connect(self, rtsp_url: str) -> bool:
        """
        Open a connection to the RTSP camera stream.
        If connection fails or a mock URL is provided, falls back to a simulated mock mode.
        """
        self.rtsp_url = rtsp_url
        logger.info(f"RTSP Service: Connecting to {rtsp_url}...")

        # Detect local/mock configs
        if rtsp_url.startswith("mock://") or "localhost" in rtsp_url or "127.0.0.1" in rtsp_url:
            self.is_mock = True
            logger.info("RTSP Service: Mock stream detected. Operating in simulation mode.")
            return True

        try:
            self.cap = cv2.VideoCapture(rtsp_url)
            if self.cap.isOpened():
                logger.info("RTSP Service: Successfully established stream connection.")
                return True
            else:
                logger.warning("RTSP Service: Could not open connection. Falling back to simulation mode.")
                self.is_mock = True
                self.cap = None
                return True
        except Exception as e:
            logger.error(f"RTSP Service: Exception occurred while connecting: {e}. Falling back to simulation.")
            self.is_mock = True
            self.cap = None
            return True

    def capture_frame(self) -> np.ndarray:
        """
        Capture a single frame from the camera stream.
        Returns a numpy array representing the image. Generates a placeholder image if mock.
        """
        logger.info("RTSP Service: Capturing frame snapshot...")

        if not self.is_mock and self.cap is not None:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    logger.info("RTSP Service: Frame captured successfully from feed.")
                    return frame
                else:
                    logger.warning("RTSP Service: Stream read returned empty. Generating mockup frame.")
            except Exception as e:
                logger.error(f"RTSP Service: Error during reading stream: {e}")

        # Fallback / Mock mode: Create a dummy 640x480 color image simulating a warehouse environment
        logger.info("RTSP Service: Generating mock warehouse frame.")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Draw dark warehouse floor and wall boundaries
        cv2.rectangle(frame, (0, 0), (640, 480), (30, 20, 20), -1)  # dark background
        cv2.rectangle(frame, (0, 200), (640, 480), (70, 70, 70), -1) # floor grey

        # Draw mock storage container/boxes (blue-ish boxes representing storage material)
        cv2.rectangle(frame, (100, 180), (220, 380), (120, 80, 50), -1) # brown crate
        cv2.rectangle(frame, (350, 220), (520, 380), (150, 100, 60), -1) # brown crate
        cv2.rectangle(frame, (120, 100), (200, 180), (20, 50, 180), -1) # blue box on top

        # Text labels on the image
        cv2.putText(frame, "CCTV LIVE FEED [SIMULATOR]", (30, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"SOURCE: {self.rtsp_url}", (30, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        return frame

    def disconnect(self) -> None:
        """
        Close the stream connection and release resources.
        """
        logger.info("RTSP Service: Disconnecting stream...")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_mock = False
        logger.info("RTSP Service: Stream disconnected successfully.")
