import cv2
import mediapipe as mp


def is_sitting(results):
    # Criteria for sitting posture
    # Check if hips are below knees are bent
    left_hip_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP].y
    right_hip_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP].y
    left_knee_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_KNEE].y
    right_knee_y = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_KNEE].y

    hip_height = (left_hip_y + right_hip_y) / 2
    knee_height = (left_knee_y + right_knee_y) / 2

    # print('Hip: ', hip_height, 'Knee: ', knee_height)
    if knee_height < hip_height or hip_height == knee_height:
        return True
    else:
        return False


def main():
    # Load the video
    video_path = "assets/v1.mp4"
    cap = cv2.VideoCapture(video_path)

    # Initialize MediaPipe Pose Detection
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    while cap.isOpened():
        # Read frame from the video
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the image to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect poses in the frame
        results = pose.process(frame_rgb)

        # Draw pose landmarks on the frame
        if results.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Determine if the person is sitting or not
        if results.pose_landmarks:
            if is_sitting(results):
                print('Sitting')
                cv2.putText(frame, "Sitting", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            else:
                print('Standing')
                cv2.putText(frame, "Standing", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Display the frame
        cv2.imshow('Sitting Pose Detection', frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
