import  cv2 as cv
import os

def extract_frame_from(video_path):
    try:
        cam = cv.VideoCapture(video_path)
        if not cam.isOpened():
            return None

        ret, frame = cam.read()
        if ret:
            frame_path = os.path.join('..\\EmployeeImages\\', f'akhroot.jpg')
            cv.imwrite(frame_path, frame)
            return frame_path
        else:
            return None
    except Exception as e:
        print(f"Error extracting frame: {e}")
        return None
    finally:
        cam.release()

def is_industry_employee():
    pass