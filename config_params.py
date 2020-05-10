import json
import os.path

import logging.config
from logger import logger_config

logging.config.dictConfig(logger_config)
logger = logging.getLogger('app_logger')

class ConfigParams(object):
	data = []
	data.append({
		"version": 0.1,
		"user_name": "user",
		"camera": 0,
		"ear_threashold": 0.27,
		"reduce_image": 0.75,
		"show_video": 0,
		"seconds_to_detect_drowsiness": 2,
		"frames_to_calculate_fps": 4,
		"keep_log_files_days": 10,
		"path_to_logfile": ".",
		"wav_file": "alarm.wav",
		"detect_on_start": 1
		})
	def __new__(cls):
		if not hasattr(cls, 'instance'):
			cls.instance = super(ConfigParams, cls).__new__(cls)
			cls.instance.config_file(file='config.json')
		return cls.instance

	def config_save(self, file='config.json'):
		try:
			with open(file, 'w') as f:
				ConfigParams.data[0]['camera HELP'] = 'Camera on host. 0 - built-in, 1 - plugged, etc'
				ConfigParams.data[0]['ear_threashold HELP'] = 'Threashold to detect drowsiness. Range [0.1, 0.4]. Step 0.01'
				ConfigParams.data[0]['reduce_image HELP'] = 'Reduce captured image. Must be in [0.25 0.5 0.75 1] -> [worse_quality better_quality]'
				ConfigParams.data[0]['show_video HELP'] = '1 - show video. 0 - do not'
				ConfigParams.data[0]['seconds_to_detect_drowsiness HELP'] = 'Must be in [1 2 3]'
				ConfigParams.data[0]['frames_to_calculate_fps HELP'] = 'values [4 .. 10]'
				ConfigParams.data[0]['keep_log_files_days HELP'] = 'values [1 .. 365]'
				ConfigParams.data[0]['path_to_logfile HELP <not implemented>'] = 'path to logfile'
				ConfigParams.data[0]['wav_file HELP <not implemented>'] = 'path to alarm audio file'
				ConfigParams.data[0]['detect_on_start HELP'] = '1 - detect drowsiness. 0 - do not'
				json.dump(ConfigParams.data[0], f, indent=4)
		except:
			logger.info('Could not save configuration file')
			return

	def config_file(self, file='config.json'):
		try:
			with open(file, 'r') as f:
				ConfigParams.data.append(json.load(f))
		except:
			logger.info('Could not load configuration file. Using default parameters')
			return
		
		# parse all keys
		if ConfigParams.data[1]['camera'] in [0, 1, 2]:
			ConfigParams.data[0]['camera'] = ConfigParams.data[1]['camera']
		if (ConfigParams.data[1]['ear_threashold'] >= .1) and (ConfigParams.data[1]['ear_threashold'] <= .4):
			ConfigParams.data[0]['ear_threashold'] = ConfigParams.data[1]['ear_threashold']
		if ConfigParams.data[1]['reduce_image'] >= .25 and ConfigParams.data[1]['reduce_image'] <= 1.0:
			ConfigParams.data[0]['reduce_image'] = ConfigParams.data[1]['reduce_image']
		if ConfigParams.data[1]['show_video'] in [0, 1]:
			ConfigParams.data[0]['show_video'] = ConfigParams.data[1]['show_video']
		if ConfigParams.data[1]['seconds_to_detect_drowsiness'] in [1, 2, 3]:
			ConfigParams.data[0]['seconds_to_detect_drowsiness'] = ConfigParams.data[1]['seconds_to_detect_drowsiness']
		if ConfigParams.data[1]['frames_to_calculate_fps'] >= 4 and ConfigParams.data[1]['frames_to_calculate_fps'] <= 10:
			ConfigParams.data[0]['frames_to_calculate_fps'] = ConfigParams.data[1]['frames_to_calculate_fps']
		if ConfigParams.data[1]['keep_log_files_days'] >= 1 and ConfigParams.data[1]['keep_log_files_days'] <= 365:
			ConfigParams.data[0]['keep_log_files_days'] = ConfigParams.data[1]['keep_log_files_days']
		if os.path.exists(ConfigParams.data[1]['path_to_logfile']):
			ConfigParams.data[0]['path_to_logfile'] = ConfigParams.data[1]['path_to_logfile']
		if os.path.exists(ConfigParams.data[1]['wav_file']):
			ConfigParams.data[0]['wav_file'] = ConfigParams.data[1]['wav_file']
		if ConfigParams.data[1]['detect_on_start'] in [0, 1]:
			ConfigParams.data[0]['detect_on_start'] = ConfigParams.data[1]['detect_on_start']

if __name__ == "__main__":
	s = ConfigParams()
	s1 = ConfigParams()

	s.data[0]['user_name'] = '100'
	print(s.data[0]['user_name'])
	print(s1.data[0]['user_name'])
		
# python config_params.py