import pyodbc
import cv2
import tensorflow as tf
import time
import os
import urllib
import datetime
import time

from inferenceutils import *

path_file = os.getcwd().replace("\\", "/")+"/"

#สร้างพาสเวิด
password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
#เพิ่ม user และ password ใน URL
top_level_url = "http://192.168.1.70/"
password_mgr.add_password(None, top_level_url, 'admin', 'admin')
handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
opener = urllib.request.build_opener(handler)

#ตัวแปรเก็บ URL
Clean_start = 'http://192.168.1.70/cgi-bin/hi3510/ytright.cgi'
Clean_stop = 'http://192.168.1.70/cgi-bin/hi3510/ytleft.cgi'

labelmap_path = "C:/Users/PTF/quality_pl2/labelmap.pbtxt"
category_index = label_map_util.create_category_index_from_labelmap(labelmap_path, use_display_name=True)
tf.keras.backend.clear_session()
model = tf.saved_model.load("C:/Users/PTF/quality_pl2/saved_model")

# #connect database
# connect = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server}; SERVER=DESKTOP-Q8GM0E3; DATABASE=com_vision_quality; UID=sa; PWD=123456")
# cursor = connect.cursor()

#connect database PL
connect = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server}; SERVER=192.168.1.2; DATABASE=com_vision_quality; UID=dbPL; PWD=dbPL")
cursor = connect.cursor()



def select_sampling_success():
    cursor.execute("select * from com_vision_quality_pl where id=2")
    row = cursor.fetchone()
    return row[1]

def update_sampling_success(value_screen):
    cursor.execute("update com_vision_quality_pl set sampling_success=? where id=2", (value_screen))
    cursor.commit()

def update_status(values_status):
    cursor.execute("update com_vision_quality_pl set status=? where id=2",(values_status))
    cursor.commit()

def select_run_process():
    cursor.execute("select * from com_vision_quality_pl where id=2")
    row = cursor.fetchone()
    return row[3]

def detect_pellet(img_for_process):
        image_np = load_image_into_numpy_array(img_for_process)
        output_dict = run_inference_for_single_image(model, image_np)
        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            category_index,
            instance_masks=output_dict.get('detection_masks_reframed', None),
            use_normalized_coordinates=True,
            skip_labels=False,
            skip_scores=True,
            min_score_thresh=0.5,
            line_thickness=2)
        image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        cv2.imwrite(path_file+"picture/img.png", image_np)
        
        return output_dict['detection_scores'], image_np
    
def time_stamp():
    return time.strftime("%d""_""%m""_""%y""_""%H""-""%M""-""%S")

while True:
    print("wait sampling =".title(), time_stamp())
    img_to_detect = False
    detect_picture_success = False
    check_sampling_success = 0

    # try:
    check_sampling_success = select_sampling_success()
    check_run_process = select_run_process()
    # except:
    #     error_check_screen_finish = "error can't select database for check screen finish".title()
    #     print(error_check_screen_finish.title())
        
    if check_sampling_success == 1 and check_run_process == 1:
        print("START PROCESS {}".format(datetime.datetime.now()))
        update_status(0)

        try:
            opener.open(Clean_start)
            urllib.request.install_opener(opener)
            time.sleep(1)
            opener.open(Clean_stop)
            urllib.request.install_opener(opener) 
            time.sleep(10)
        except:
            pass

        try:
            update_status(0)
            os.remove("C:/Users/PTF/quality_pl2/img_for_process/img_for_process.png")
            remove_pic_success = "remove picuture success"
            print(remove_pic_success.title())
        except:
            error_remove_picture = "not picture in folder"
            print(error_remove_picture.title())

        cap = cv2.VideoCapture('rtsp://admin:admin@192.168.1.70:554/11')
        try:
            while True:
                _, frame = cap.read()
                frame_crop = frame[140:700, 350:1280, :]
                cv2.imwrite("C:/Users/PTF/quality_pl2/img_for_process/img_for_process.png", frame_crop)
                cv2.imwrite("C:/Users/PTF/quality_pl2/img_for_train/img_train_{}.png".format(time_stamp()), frame_crop)
                break
        except:
            error_connect_camera = "not connect camera for detect"
            print(error_connect_camera.title())

        try:
            img_for_process = "C:/Users/PTF/quality_pl2/img_for_process/img_for_process.png"
            img_to_detect = detect_pellet(img_for_process)
            cv2.imwrite("C:/Users/PTF/quality_pl2/img_process_success/img_{}.png".format(time_stamp()), img_to_detect[1])
            cv2.imwrite("C:/Users/PTF/quality_pl2/img_for_show/img_show.png", img_to_detect[1])
            detect_picture_success = True
        except:
            for round_not_picture in range(5):
                try:
                    error_for_detect = "error not find picture in folder for detect !!!"
                    print(error_for_detect.title())
                    update_status(3)
                    break
                except:
                    error_for_values = "error not update values to database"
                    print(error_for_values.title())
                time.sleep(5)
        
        if detect_picture_success == True:
            count_values = 0
            for values_ng in  img_to_detect[0] > 0.5:
                if values_ng == True:
                    count_values += 1

            print("count values =", count_values)
            
            if count_values < 6:
                for update_values in range(5):
                    try:
                        update_status(1)
                        print("update values for process success".title())
                        break
                    except:
                        print("error ; can't update values".title())
                    time.sleep(10)
                time.sleep(30)

            elif count_values >= 6:
                for update_values_ng in range(5):
                    try:
                        update_status(2)
                        print("update values for process success".title())
                        # cv2.imshow("", img_to_detect[1])
                        # cv2.waitKey(5000)
                        cv2.destroyAllWindows()
                        break
                    except:
                        print("can't update values".title())
                    time.sleep(10)
                time.sleep(30)

            update_sampling_success(0)
        print("END PROCESS {}".format(datetime.datetime.now()))
    print("-----------------------------------------------")

    time.sleep(10)