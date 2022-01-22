from canvasapi import Canvas
import requests

#important data in order to connect to my canvas profile
#https://learninganalytics.ubc.ca/for-students/canvas-api/
#sensitive information
with open('sensitive_data.txt') as f:
    lines = f.readlines()

API_URL = lines[0]
API_KEY = lines[1]
API_HABI_USER = lines[5].rstrip("\n")
API_HABI_KEY = lines[6].rstrip("\n")

#all this information im getting from API_URL/api/v1/courses/ 
# by manualy selecting my id and semester
USER_ID = int(lines[2])
CURRENT_TERM = int(lines[3])
canvas = Canvas(API_URL, API_KEY)

#authentication header for Habitica API
auth_headers = {'x-api-user': API_HABI_USER, 'x-api-key': API_HABI_KEY}

########## CANVAS API
#### LETS GET THE ASSIGNMENTS FROM CANVAS ####
def get_valid_homework (course_id):
	test_course = canvas.get_course(course_id)
	valid_homework = []
	print('Getting assignments from ', test_course.name)
	#get the list of all future homework
	all_homework = test_course.get_assignments(bucket='future')
	for assign in all_homework:
		#we need to filter all assignments that were already submitted
		if assign.name != 'Roll Call Attendance':
			valid_homework.append(assign)
	return valid_homework

#### LETS GET MY HOMEWORK STILL DUE ####
def get_my_homework(user):
	classes = []	#id for current/interested classes
	valid_homework = []
	#lets get all classes im enrolled at
	all_classes = user.get_courses(enrollment_state='active') 

	for c in all_classes: 
		## we filter all active classes from other semesters
		if c.enrollment_term_id == CURRENT_TERM:
			classes.append(c.id)
			#now we collect the valid homework
			valid_homework = valid_homework + get_valid_homework(c)
	return valid_homework

#### QUICK FORMATING FOR HOMEWORK ####
def basic_info_homework( valid_homework):
	for hw in valid_homework:
		print(hw.name,' | ', hw.due_at,' | ', hw.has_submitted_submissions, ' | ', hw.id)	

#### LETS GET MY USER INFORMATION FROM CANVAS####
def get_myself():
	user = canvas.get_user(USER_ID)
	print('Wellcome back ',user.name,'!\n')
	return user

########## HABITICA API
#### GET THE TADID FOR THE CANVAS TAGS ####
def get_Canvas_tagId():
	r = requests.get(
	  'https://habitica.com/api/v3/tags',
	  headers=auth_headers)
	assert r.status_code == 200
	CanvasId = ''
	for tag in r.json()['data']:
		if 'Canvas' == tag['name']:
			CanvasId = tag['id']
			break
	return CanvasId

#### GET ALL VALID TODOS FROM HABITICA ####
def get_current_todos(canvasId):
	r = requests.get(
	  'https://habitica.com/api/v3/tasks/user?type=todos',
	  headers=auth_headers)
	assert r.status_code == 200

	todos = {}
	for todo in r.json()['data']:
		if canvasId in todo['tags']: 
			date = todo['date']
			if (date != None):
				date = date[0:len(date)-5]+date[len(date)-1]
			todos[todo['notes']] = [todo['text'], todo['id'], date]
	return todos

#### LETS START POSTING SOME TASK ####
def post_new_todo(taskJson):
	r = requests.post( 'https://habitica.com/api/v3/tasks/user',
	  json=taskJson,
	  headers=auth_headers)
	assert r.status_code == 201, r.json()

#### UPDATING SOME TASK ####
def put_todo(taskJson, taskId):
	r = requests.put( 'https://habitica.com/api/v3/tasks/' + str(taskId),
	  json=taskJson,
	  headers=auth_headers)
	assert r.status_code == 200, r.json()

########## MAIN
#### SYNCH THE DATA ####
user = get_myself()

#all homework still pending to do
valid_homework = get_my_homework(user)
print('\nCollecting all due homework from Canvas')
basic_info_homework(valid_homework)

#all homework that was already uploaded
canvasId = get_Canvas_tagId()
uploaded_homework = get_current_todos(canvasId)

print('\nStarting to upload homework to habitica')
#is pending homework already uploaded
for hw in valid_homework:
	upload_hw = True
	if str(hw.id) in uploaded_homework.keys():
		#its still up in habitica 
		#if is still in habitica, check if due date needs any update
		if hw.due_at != uploaded_homework[str(hw.id)][2]:
			print(hw.name,' needs a due_at update')
			taskJson={ "text": hw.name, "type": "todo", "notes": hw.id, "priority": 2, "tags": [canvasId], "date":hw.due_at}
			put_todo(taskJson, uploaded_homework[str(hw.id)][1])
		else:
			print(hw.name,' is still active on Habitica')
		upload_hw = False
	else:
		#if its not in habitica, it maybe have been completed
		#and its on the log of uploaded ids
		with open('uploaded_id.txt') as f:
		    for line in f:
		    	if str(hw.id) == line.rstrip("\n"):
		    		print(hw.name,' was already uploaded to Habitica')
		    		upload_hw = False
		    		break
	if upload_hw:
		#if its not in the log, its a new task and needs to be uploaded
		taskJson={ "text": hw.name, "type": "todo", "notes": hw.id, "priority": 2, "tags": [canvasId], "date":hw.due_at}
		post_new_todo(taskJson)
		f = open("uploaded_id.txt", "a")
		f.write(str(hw.id)+'\n')
		f.close()
		print(hw.name,' submited to Habitica')