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
def get_valid_homework (course_id):
    ''' LETS GET THE ASSIGNMENTS FROM CANVAS '''
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

def get_my_homework(user):
    ''' LETS GET MY HOMEWORK STILL DUE '''
    classes = []	#id for current/interested classes
    valid_homework = []
    #lets get all classes im enrolled at
    all_classes = user.get_courses(enrollment_state='active') 

    for course in all_classes: 
        ## we filter all active classes from other semesters
        if course.enrollment_term_id == CURRENT_TERM:
            classes.append(course.id)
            #now we collect the valid homework
            valid_homework = valid_homework + get_valid_homework(course)
    return valid_homework

def basic_info_homework( valid_homework):
    ''' QUICK FORMATING FOR HOMEWORK '''
    for habitica_hw in valid_homework:
        print(habitica_hw.name,' | ', habitica_hw.due_at,
            ' | ', habitica_hw.has_submitted_submissions, 
            ' | ', habitica_hw.id)	

def get_myself():
    ''' LETS GET MY USER INFORMATION FROM CANVAS'''
    user = canvas.get_user(USER_ID)
    print('Wellcome back ',user.name,'!\n')
    return user

########## HABITICA API
def get_canvas_tag_id():
    ''' GET THE TADID FOR THE CANVAS TAGS '''
    request = requests.get(
      'https://habitica.com/api/v3/tags',
      headers=auth_headers)
    assert request.status_code == 200
    canvas_id = ''
    for tag in request.json()['data']:
        if 'Canvas' == tag['name']:
            canvas_id = tag['id']
            break
    return canvas_id

def get_current_todos(canvas_id):
    ''' GET ALL VALID TODOS FROM HABITICA '''
    request = requests.get(
      'https://habitica.com/api/v3/tasks/user?type=todos',
      headers=auth_headers)
    assert request.status_code == 200

    todos = {}
    for todo in request.json()['data']:
        if canvas_id in todo['tags']: 
            date = todo['date']
            if date is not None:
                date = date[0:len(date)-5]+date[len(date)-1]
            todos[todo['notes']] = [todo['text'], todo['id'], date]
    return todos

def post_new_todo(task_json):
    ''' LETS START POSTING SOME TASK '''
    request = requests.post( 'https://habitica.com/api/v3/tasks/user',
	  json=task_json,
	  headers=auth_headers)
    assert request.status_code == 201, request.json()

def put_todo(task_json, task_id):
    ''' UPDATING SOME TASK '''
    request = requests.put( 'https://habitica.com/api/v3/tasks/' + str(task_id),
	  json=task_json,
	  headers=auth_headers)
    assert request.status_code == 200, request.json()

########## MAIN
#### SYNCH THE DATA ####
user = get_myself()

#all homework still pending to do
valid_homework = get_my_homework(user)
print('\nCollecting all due homework from Canvas')
basic_info_homework(valid_homework)

#all homework that was already uploaded
canvas_id = get_canvas_tag_id()
uploaded_homework = get_current_todos(canvas_id)

print('\nStarting to upload homework to habitica')
#is pending homework already uploaded
for habitica_hw in valid_homework:
    UPLOAD_HW = True
    if str(habitica_hw.id) in uploaded_homework.keys():
		#its still up in habitica 
		#if is still in habitica, check if due date needs any update
        if habitica_hw.due_at != uploaded_homework[str(habitica_hw.id)][2]:
            print(habitica_hw.name,' needs a due_at update')
            task_json={ 
                "text": habitica_hw.name, 
                "type": "todo", "notes": habitica_hw.id, 
                "priority": 2, "tags": [canvas_id], 
                "date":habitica_hw.due_at
            }
            put_todo(task_json, uploaded_homework[str(habitica_hw.id)][1])
        else:
            print(habitica_hw.name,' is still active on Habitica')
        UPLOAD_HW = False
    else:
		#if its not in habitica, it maybe have been completed
		#and its on the log of uploaded ids
        with open('uploaded_id.txt') as f:
            for line in f:
                if str(habitica_hw.id) == line.rstrip("\n"):
                    print(habitica_hw.name,' was already uploaded to Habitica')
                    UPLOAD_HW = False
                    break
    if UPLOAD_HW:
		#if its not in the log, its a new task and needs to be uploaded
        task_json={
            "text": habitica_hw.name, 
            "type": "todo", 
            "notes": habitica_hw.id, 
            "priority": 2, 
            "tags": [canvas_id], 
            "date":habitica_hw.due_at
        }
        post_new_todo(task_json)
        f = open("uploaded_id.txt", "a")
        f.write(str(habitica_hw.id)+'\n')
        f.close()
        print(habitica_hw.name,' submited to Habitica')
