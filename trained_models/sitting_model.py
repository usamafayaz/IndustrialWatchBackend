import cv2
import mediapipe as mp


def is_sitting(results, height):
    # Criteria for sitting posture
    # Check if hips are slightly above or at the level of knees
    left_hip_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP].y
    right_hip_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP].y
    left_knee_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_KNEE].y
    right_knee_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_KNEE].y

    hip_height = (left_hip_y + right_hip_y) / 2
    knee_height = (left_knee_y + right_knee_y) / 2
    # Calculate the margin based on the height of the person
    margin = height * 0.08  # Adjust the multiplier as needed

    # Check if the knees are slightly lower than the hips
    return knee_height < hip_height + margin



def sitting_detection_(frame):
    # Initialize MediaPipe Pose Detection
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7)
    drawing_utils = mp.solutions.drawing_utils
    # Convert the image to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect poses in the frame
    results = pose.process(frame_rgb)

    # Draw pose landmarks on the frame
    if results.pose_landmarks:
        drawing_utils.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),  # Red connections
            drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)  # Green keypoints
        )

    # Determine if the person is sitting or not
    if results.pose_landmarks:
        height = calculate_height(results)
        if is_sitting(results, height):
            print('Sitting')
            return True
        else:
            print('Standing')
            return False

def calculate_height(results):
    # Calculate the height of the person
    left_shoulder_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].y
    right_shoulder_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER].y
    shoulder_height = (left_shoulder_y + right_shoulder_y) / 2

    left_heel_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HEEL].y
    right_heel_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HEEL].y
    heel_height = (left_heel_y + right_heel_y) / 2

    height = 1 - (shoulder_height - heel_height)
    return height