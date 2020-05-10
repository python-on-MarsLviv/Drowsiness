from imutils.video import FileVideoStream
from imutils.video import VideoStream
from videostream import VideoStream as VideoStream1
from imutils import resize
from imutils import face_utils

import dlib
import cv2

from numpy import array
from scipy.spatial import distance as dist			
from time import sleep, perf_counter, time
from threading import Thread

from kivy.graphics.texture import Texture
from kivy.core.image import Image

import logging.config
from logger import logger_config

logging.config.dictConfig(logger_config)
logger = logging.getLogger('app_logger')

def eye_aspect_ratio(eye):
	# compute the euclidean distances between the two sets of
	# vertical eye landmarks (x, y)-coordinates
	A = dist.euclidean(eye[1], eye[5])
	B = dist.euclidean(eye[2], eye[4])

	# compute the euclidean distance between the horizontal
	# eye landmark (x, y)-coordinates
	C = dist.euclidean(eye[0], eye[3])

	# compute the eye aspect ratio (ear)
	ear = (A + B) / (2.0 * C)

	return ear

class VideoMain():
	def init_tools(self, shape_predictor
						, frames_queue
						, ear_threashold=0.3
						, reduce_image=.5
						, show_video=True
						, seconds_to_detect_drowsiness=2
						, frames_to_calculate_fps=4
						):
		self.frames_queue = frames_queue
		self.ear_threashold = ear_threashold
		self.reduce_image = reduce_image
		self.show_video = show_video
		self.seconds_to_detect_drowsiness = seconds_to_detect_drowsiness
		self.frames_to_calculate_fps = frames_to_calculate_fps
		self.fake_frame = array([1,1,1,3])

		# initialize dlib's face detector (HOG-based) and then create
		# the facial landmark predictor
		self.detector = dlib.get_frontal_face_detector()
		try:
			logger.info('loading facial landmark predictor...')
			self.predictor = dlib.shape_predictor(shape_predictor)
			logger.info('\t\t... done.')
		except:
			logger.info('could not load facial landmark predictor; raise exception ...')
			raise ValueError('could not load facial landmark predictor')
		# grab the indexes of the facial landmarks for the left and
		# right eye, respectively
		(self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
		(self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

		self.ear_consecutive_frames = 20
		self.drowsiness_counter = 0
		self.fps = 0
		self.looping = False # flag to show that start_process_loop() method running

		self.err_read_frame = False # error occured during frame reading
		self.err_processing_frame = False# error occured during frame processing

	def start_stream(self):
		self.vs.start()

	def stop_stream(self):
		self.vs.stop()

	def init_stream(self, camera=0):
		if type(camera) == type(1):
			self.camera = camera;
			self.web_cam = True
			self.file = ''
			try: 
				self.vs = VideoStream1(self.camera)
				self.err_open_stream = False
			except:
				self.err_open_stream = True
				logger.info('can not open stream')
		elif type(camera) == type('string'):
			self.camera = -1;
			self.web_cam = False 		
			self.file = camera
			try:
				self.vs = FileVideoStream(self.file)
				self.err_open_stream = False
			except:
				self.err_open_stream = True
				logger.info('can not open file')

		#sleep(0.1)						# time to worm-up camera

		self.processed_frames = 0# number of processed frames in current time window	

	def stop_process_loop(self):
		self.looping = False
		self.thread_process_loop.join();

	def start_process_loop(self):
		self.looping = True
		ear = 0.5
		tic = perf_counter()
		alarm_state = False
		while  self.looping:
			# if this is a file video stream, then we need to check if
			# there any more frames left in the buffer to process
			if not self.web_cam and not self.vs.more():
				logger.info('web cam terminated')
				break

			try:
				frame = self.vs.read()
				self.processed_frames += 1
			except:
				self.err_read_frame = True
				logger.info('can not read frame')
				continue
			try:
				quality_width = int(frame.shape[1] * self.reduce_image)
			except:
				logger.info('frame not available')
				continue
			frame = resize(frame, width=quality_width)
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

			# detect faces in the grayscale frame
			rects = self.detector(gray, 0)
			# loop over the face detections
			for rect in rects:
				# determine the facial landmarks for the face region, then
				# convert the facial landmark (x, y)-coordinates to a NumPy
				# array
				shape = self.predictor(gray, rect)
				shape = face_utils.shape_to_np(shape)

				# extract the left and right eye coordinates, then use the
				# coordinates to compute the eye aspect ratio for both eyes
				leftEye = shape[self.lStart:self.lEnd]
				rightEye = shape[self.rStart:self.rEnd]
				leftEAR = eye_aspect_ratio(leftEye)
				rightEAR = eye_aspect_ratio(rightEye)

				# average the eye aspect ratio together for both eyes
				ear = (leftEAR + rightEAR) / 2.0

				# compute the convex hull for the left and right eye, then
				# visualize each of the eyes
				leftEyeHull = cv2.convexHull(leftEye)
				rightEyeHull = cv2.convexHull(rightEye)
				cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
				cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

				if ear < self.ear_threashold:
					self.drowsiness_counter += 1
					if self.drowsiness_counter >= self.ear_consecutive_frames:
						alarm_state = True
						
				else:
					self.drowsiness_counter = 0
					alarm_state = False
			
			if not self.frames_queue.full():
				if self.show_video:
					self.frames_queue.put((alarm_state, self.fps, ear, frame))
				else:
					self.frames_queue.put((alarm_state, self.fps, ear, self.fake_frame))

			if not (self.processed_frames % self.frames_to_calculate_fps):
				toc = perf_counter()
				self.fps = int(self.processed_frames // (toc - tic))
				self.processed_frames = 0
				tic = toc
				self.ear_consecutive_frames = self.fps * self.seconds_to_detect_drowsiness

		self.vs.stop();

	def set_camera(self, camera):
		self.camera = camera

	@staticmethod
	def get_registered_cameras():
		cameras = []
		for i in range(10):
			stream = cv2.VideoCapture(i)
			if stream is None or not stream.isOpened():
				stream.release()
				return cameras
			else:
				cameras.append(i)
				stream.release()

		return cameras
	
	def start(self, camera=0):
		self.init_stream(camera)
		self.thread_process_loop = Thread(target=self.start_process_loop, args=())
		#self.thread_process_loop.daemon = True # https://github.com/jrosebr1/imutils/issues/38
		self.start_stream()
		self.thread_process_loop.start()

	def stop(self):
		self.stop_process_loop()
	

