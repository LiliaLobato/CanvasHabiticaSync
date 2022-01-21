from canvasapi import Canvas

#important data in order to connect to my canvas profile
#https://learninganalytics.ubc.ca/for-students/canvas-api/
#sensitive information
with open('sensitive_data.txt') as f:
    lines = f.readlines()

API_URL = lines[0]
API_KEY = lines[1]
#all this information im getting from API_URL/api/v1/courses/
USER_ID = int(lines[2])
CURRENT_TERM = int(lines[3])
canvas = Canvas(API_URL, API_KEY)


#### LETS GET THE ASSIGNMENTS ####
def get_valid_homework (course_id):
	test_course = canvas.get_course(course_id)
	valid_homework = []
	print('Getting assignments from ', test_course.name)
	#get the list of all homework
	all_homework = test_course.get_assignments()
	for assign in all_homework:
		#we need to filter all assignments that were already submitted
		if assign.has_submitted_submissions == False:
			valid_homework.append(assign)
	return valid_homework

#### QUICK FORMATING FOR HOMEWORK ####
def basic_info_homework( valid_homework):
	for hw in valid_homework:
		print(hw.name,' | ', hw.due_at,' | ', hw.has_submitted_submissions, ' | ', hw.id)	

#### LETS GET MY USER INFORMATION ####
user = canvas.get_user(USER_ID)
print('Wellcome back ',user.name,'\n')

#### LETS GET THE COURSE INFORMATION ####
classes = []		#id for current/interested classes
valid_homework = [] #all homework still pending to do
#lets get all classes im enrolled at
all_classes = user.get_courses(enrollment_state='active') 

for c in all_classes: 
	## we filter all active classes from other semesters
	if c.enrollment_term_id == CURRENT_TERM:
		classes.append(c.id)
		#now we collect the valid homework
		valid_homework = valid_homework + get_valid_homework(c)

basic_info_homework(valid_homework)