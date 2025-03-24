import re
import threading
import requests

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.filechooser import FileChooserIconView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.animation import Animation
from kivy.properties import StringProperty
from kivy.graphics import Line
from kivy.uix.image import AsyncImage
from kivy.uix.behaviors import ButtonBehavior

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.list import OneLineListItem, TwoLineIconListItem, IconLeftWidget, ImageLeftWidget, OneLineAvatarListItem
from kivymd.uix.label import MDIcon
from kivymd.uix.button import MDIconButton
from kivymd.uix.widget import MDWidget
from kivymd.utils.set_bars_colors import set_bars_colors

import google.generativeai as genai

import os
import base64
import pandas as pd
from bs4 import BeautifulSoup

Window.size = (310, 580)

#BASE_URL = 'https://cropcareserver.onrender.com/abcd/'
BASE_URL = 'http://0.0.0.0:8000/abcd/'
REGISTER_URL = BASE_URL + 'register/'
EMAIL_REGISTER_URL=BASE_URL+'emailregister/'
FORGET_PASSWOD_URL=BASE_URL+'forgetpassword/'
LOGIN_URL = BASE_URL + 'login/'

POST_URL = BASE_URL+'posts/'
PROFILE_URL = BASE_URL+'profile/'
UPDATE_PROFILE_URL = BASE_URL+'updateprofile/'
SCHEMES_URL=BASE_URL+'schemes/'
SCHEME_DETAIL_URL=BASE_URL+'schemedetail/'
SHOPPING_URL=BASE_URL+'shopping/'
FEEDBACK_URL=BASE_URL+'feedback/'
CONTACT_US_URL=BASE_URL+'contactus/'


CURRENT_USER = "yogi"
CURRENT_USER_PASSWORD = ""
SCHEME_ID=None
POST_ID_LIST=[]
PRODUCT_ID_LIST=[]
PRODUCT_TYPE_LIST=[]

SCREEN_TRACKER=[]

CROP_BASE_URL = "https://www.apnikheti.com"

LEGAL_NOTICE_TEXT = """
LEGAL NOTICE

Terms of Service:
    - By using this application, you agree to the terms and conditions outlined here.
    - We reserve the right to update the terms at any time without prior notice.

Privacy Policy:
    - We value your privacy and commit to safeguarding your personal information.
    - Your data will not be shared with third parties without your consent.

Limitation of Liability:
    - The application is provided as-is. We are not responsible for any loss or damage resulting from its use.
    
Governing Law:
    - These terms are governed by the laws of the jurisdiction where the application is provided.

Contact Information:
    - For more information, please contact us at support@cropcare.com.
"""

def get_image(file_name,base64_image):
    with open(file_name, "wb") as image_file:
        image_file.write(base64.b64decode(base64_image))

def decode_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    return image_base64

class Separator(MDWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Line(points=[0, 0, self.width, 0], width=1)

class StartUpScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.animate_logo, 0.5)

    def animate_logo(self, *args):
        logo_image = self.ids.logo_image
        animation = Animation(
            opacity=1, 
            duration=2,
        )
        animation.start(logo_image)

class LoginScreen(MDScreen):
    password_eye = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password_eye = True

    def login(self):
        self.dialog = None
        uname = self.ids.username.text
        psd = self.ids.password.text
        
        if not uname or not psd:
            self.show_dialog("Error", "Please fill in both username and password.")
            return
        
        login_data = {
            'username': uname,
            'password': psd
        }
        try:
            response = requests.post(LOGIN_URL, json=login_data)
            if response.status_code == 200:
                res = response.json()
                global CURRENT_USER, CURRENT_USER_PASSWORD
                CURRENT_USER = uname
                CURRENT_USER_PASSWORD = psd
                self.manager.current = "welcome" 
            else:
                res = response.json()
                error_message = res.get('message', "Username/Password doesn't exist...")
                self.show_dialog("Failed", error_message)
                
        except requests.exceptions.RequestException:
            self.show_dialog("Error", "Server is not responding...")
            
        except Exception as e:
            print("(LoginScreen) Error:", e)
            self.show_dialog("Error", "An unexpected error occurred. Please try again.")

    def show_dialog(self, tit="Alert!!", txt="..."):
        if self.dialog is None:
            self.dialog = MDDialog(
                title=str(tit),
                text=str(txt),
                buttons=[
                    MDFlatButton(
                        text='OK', text_color=self.theme_cls.primary_color,
                        on_release=self.close_dialog,
                    ),
                ]
            )
        self.dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()

    def password_eye_visibility(self):
        self.password_eye = not self.password_eye 

    def switch_to_signup(self):
        self.manager.current = "signup" 

    def clear_error_message(self):
        self.ids.error_message.text = "" 

    def forgetPassword(self):
        self.manager.current = 'forgetpassword'

class ForgetPasswordScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog = None

    def forget(self):
        email = self.ids.email.text
        
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        
        if not re.match(email_regex, email):
            self.show_password_dialog("Alert", "Please enter a valid email address.")
            return

        try:
            response = requests.post(FORGET_PASSWOD_URL, data={'email': email})

            if response.status_code == 200:
                self.show_password_dialog("Success", f"Check your email: {email} to reset your password.")
            else:
                error_message = f"Failed: {response.status_code}. Please try again later."
                self.show_password_dialog("Server Error", error_message)

        except requests.exceptions.RequestException as e:
            print("(Forget) Exception:", e)
            self.show_password_dialog("Error", "Server is not responding...\nPlease try again later.")

        except Exception as e:
            print("(Forget) Unexpected error:", e)
            self.show_password_dialog("Error", "An unexpected error occurred. Please try again later.")

    def show_password_dialog(self, title="Password", password="Your password has been sent to your email."):
        if self.dialog is None:
            self.dialog = MDDialog(
                title=title,
                text=password,
                buttons=[
                    MDFlatButton(
                        text="CLOSE",
                        on_release=lambda x: self.close_dialog(),
                    ),
                ],
            )
        self.dialog.open()

    def close_dialog(self):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    def go_back(self):
        if len(SCREEN_TRACKER) > 1:
            self.manager.current = SCREEN_TRACKER[-2]
            SCREEN_TRACKER.pop()
        else:
            self.manager.current = 'login'

class SignupScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog = None

    def send_email_register(self):
        email = self.ids.email.text
        try:
            if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):

                Clock.schedule_once(lambda dt: self.show_dialog("Success", "Please check the email for further process....."))
                response = requests.post(EMAIL_REGISTER_URL, data={'email': email, 'url': BASE_URL})
                if response.status_code == 200:
                    self.manager.current='login'
                    return
                else:
                    Clock.schedule_once(lambda dt: self.show_dialog("Error", "Email registration failed."))  # Example error message
                    return
            else:
                Clock.schedule_once(lambda dt: self.show_dialog("Alert", "Please enter a valid email....."))
        except Exception as e:
            print("(Signup)Exception", e)
            Clock.schedule_once(lambda dt: self.show_dialog("Error !!", "Server is not responding...\nPlease try again"))

    def signUp(self):
        threading.Thread(target=self.send_email_register, daemon= True).start()
        
    def show_dialog(self,tit="Alert",txt="Server Error..."):
        if self.dialog == None:
            self.dialog = MDDialog(
                title=str(tit),
                text=str(txt),
                buttons=[
                    MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                    on_release=self.close_dialog),
                    ]
                )
        self.dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()

class WelcomeScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append('home') if 'home' not in SCREEN_TRACKER else None

class CircularAvatarImage(MDCard):
    avatar = StringProperty()
    name = StringProperty()

class StoryCreator(MDCard):
    avatar = StringProperty()

class PostCard(MDCard):
    profile_pic = StringProperty()
    avatar = StringProperty()
    username = StringProperty()
    post = StringProperty()
    caption = StringProperty()
    likes = StringProperty()
    comments = StringProperty()
    posted_ago = StringProperty()
     
class HomeScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        Clock.schedule_once(self.list_posts, 0)

    def list_posts(self,*args):
        try:
            global POST_ID_LIST
            response=requests.post(POST_URL,data={'CURRENT_USER':CURRENT_USER})
            self.ids.timeline.remove_widget(PostCard())
            if response.status_code == 200:                
                for i in response.json()['data']:
                    if i['post_id'] in POST_ID_LIST:
                        continue
                    else:
                        POST_ID_LIST.append(i['post_id'])
                        self.ids.timeline.add_widget(PostCard(
                            id=str(i['post_id']),
                            username=i['username'],
                            avatar=self.create_data(path=i['avtar'],value='avtar',id=i['post_id'],type='jpg'),
                            post = self.create_data(path=i['data'],value='post',id=i['post_id'],type=i['data_type'],),
                            profile_pic=self.create_data(path=i['profile_pic'],value='profile',type='jpg'),
                            caption=i['caption'],
                            likes=str(i['likes']),
                            comments=str(i['comments']),
                            posted_ago=i['posted_ago'],
                            ))
        except Exception as e :
            print("Error : ",e)
            
            
    def create_data(self,path,value,id="",type='jpg'):
        if path is not None :
            temp_file_name=str(f'Posts/{value}_{id}.{type}')
            with open(temp_file_name, "wb") as image_file:
                image_file.write(base64.b64decode(path))
            return temp_file_name
        else:
            return None
            
class FertilizerScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.area_input = ObjectProperty(None)
        self.crop_type_input = ObjectProperty(None)
        self.fertilizer_ratio_input = ObjectProperty(None)
        self.result_label = ObjectProperty(None)
        self.soil_types = ["Alluvial Soil", "Arid Soil", "Chernozem Soil", "Chestnut Soil", "Clay Soil", "Colluvial Soil",
                      "Ferralitic Soil", "Gley Soil", "Grey Soil", "Histosol (Peat Soil)", "Hydromorphic Soil", 
                      "Mollisol (Prairie Soil)", "Oxisol (Tropical Red Soil)", "Podzol Soil", "Regosol", "Andosol", 
                      "Spodosol", "Vertisol", "Calcisol", "Acrisol", "Luvisol", "Cambisol", "Phaeozem", "Plinthosol", 
                      "Rankers", "Silty Soil", "Sand Soil", "Latosol", "Tundra Soil", "Alfisol", "Ultisol", "Andosol", 
                      "Gelisol", "Histosol", "Aridisols", "Gleysols", "Inceptisols", "Mollisols", "Oxisols", "Spodosols", 
                      "Vertisols"
                      ]

    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        
    def on_search_soil(self, text):
        self.ids.result_label.text = "Select the soil type...."
        self.ids.soil_results.clear_widgets()
        self.ids.scroll.height='200dp'
        for soil in self.soil_types:
            if text.lower() in soil.lower():
                self.ids.soil_results.add_widget(
                    OneLineListItem(text=soil,
                                    height='11dp',
                                    on_press=lambda x=soil : self.display(x.text))
                )
    def display(self,soil):
        self.ids.soil_type.text=soil
        self.ids.soil_results.clear_widgets()
        self.ids.fert_button.disabled=False
        self.ids.scroll.height='1dp'
        self.ids.result_label.text = ""
        
    def calculate_fertilizer(self):
        try:
            area = int(self.ids.plant_area.text)
            soil_type = str(self.ids.soil_type.text.lower())
            self.ids.result_label.text = ""
            self.ids.fertilizer_type_label.text = ""

            if soil_type == "sandy":
                fertilizer_amount = area * 1.5
                fertilizer_type = "Nitrogen-rich fertilizer (e.g., Urea)"
            elif soil_type == "loamy":
                fertilizer_amount = area * 1.2
                fertilizer_type = "Balanced fertilizer (e.g., NPK)"
            elif soil_type == "clay":
                fertilizer_amount = area * 1.8
                fertilizer_type = "Phosphorus-rich fertilizer (e.g., Superphosphate)"
            else:
                fertilizer_amount = area * 1.5
                fertilizer_type = "General fertilizer (e.g., Compost or Organic Fertilizer)"
                
            self.ids.result_label.text = f"Fertilizer Needed: {fertilizer_amount} kg"
            self.ids.result_label.text_color=(0,1,0,1)
            self.ids.fertilizer_type_label.text = f"Recommended: {fertilizer_type}"
            self.ids.fertilizer_icon.icon = "check-circle"
        except ValueError:
            self.ids.result_label.text = "Please enter valid values."
            self.ids.fertilizer_type_label.text = ""
            self.ids.fertilizer_icon.icon = "alert-circle"

class CropsDiseaseScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disease_info = {
            "Late Blight": "Late blight is a devastating disease caused by the fungus-like organism Phytophthora infestans. It affects potatoes and tomatoes, causing dark lesions on leaves, stems, and fruits. Cool, wet weather favors its spread. Management includes crop rotation, fungicides, and resistant varieties.",
            "Powdery Mildew": "Powdery mildew is a fungal disease that affects a wide range of crops, including grapes, cucumbers, and squash. It appears as white, powdery spots on leaves and stems. Proper air circulation, fungicides, and resistant varieties help control it.",
            "Rust": "Rust is a fungal disease that causes orange, yellow, or brown pustules on leaves and stems of crops like wheat, beans, and corn. It thrives in humid conditions. Control methods include fungicides and planting resistant varieties.",
            "Fusarium Wilt": "Fusarium wilt is a soil-borne fungal disease that affects tomatoes, bananas, and cucumbers. It causes yellowing, wilting, and stunted growth. Crop rotation, soil solarization, and resistant varieties are effective management strategies.",
            "Bacterial Blight": "Bacterial blight, caused by Xanthomonas species, affects crops like rice, cotton, and beans. It causes water-soaked lesions on leaves and stems. Copper-based sprays and resistant varieties are commonly used for control.",
            "Downy Mildew": "Downy mildew is a fungal disease that affects crops like grapes, lettuce, and cucumbers. It causes yellow spots on leaves and a white, fuzzy growth underneath. Fungicides and proper spacing for air circulation are key to management.",
            "Anthracnose": "Anthracnose is a fungal disease that affects beans, tomatoes, and mangoes. It causes dark, sunken lesions on fruits, leaves, and stems. Fungicides and removing infected plant debris help control the disease.",
            "Root Rot": "Root rot is caused by various fungi and affects crops like soybeans, peas, and tomatoes. It leads to wilting, yellowing, and stunted growth. Well-drained soil and fungicides are essential for prevention.",
            "Leaf Spot": "Leaf spot is a fungal or bacterial disease that causes circular or irregular spots on leaves of crops like tomatoes, peppers, and lettuce. Proper sanitation and fungicides are effective control measures.",
            "Verticillium Wilt": "Verticillium wilt is a soil-borne fungal disease that affects strawberries, tomatoes, and potatoes. It causes yellowing, wilting, and vascular discoloration. Crop rotation and resistant varieties are recommended.",
            "Clubroot": "Clubroot is a soil-borne disease caused by Plasmodiophora brassicae, affecting cruciferous crops like cabbage and broccoli. It causes swollen, distorted roots. Liming soil and crop rotation help manage the disease.",
            "Black Rot": "Black rot is a bacterial disease that affects cruciferous vegetables like cabbage and cauliflower. It causes V-shaped yellow lesions on leaves and blackened veins. Crop rotation and copper sprays are effective.",
            "Smut": "Smut is a fungal disease that affects crops like corn and wheat. It causes black, powdery spore masses on ears or grains. Resistant varieties and crop rotation are key to control.",
            "Mosaic Virus": "Mosaic virus affects crops like tomatoes, cucumbers, and tobacco. It causes mottled, discolored leaves and stunted growth. Controlling aphids and using virus-free seeds are essential.",
            "Blast": "Blast is a fungal disease that affects rice, causing lesions on leaves, stems, and grains. It thrives in humid conditions. Resistant varieties and fungicides are used for management.",
            "Damping Off": "Damping off is a fungal disease that affects seedlings, causing them to collapse and die. It is common in tomatoes, peppers, and cucumbers. Proper sanitation and well-drained soil are crucial.",
            "Canker": "Canker is a fungal or bacterial disease that causes sunken, dead areas on stems and branches of crops like citrus and apples. Pruning infected parts and applying fungicides help control it.",
            "Scab": "Scab is a fungal disease that affects apples, potatoes, and pears. It causes rough, scaly lesions on fruits and leaves. Fungicides and resistant varieties are effective control measures.",
            "Fire Blight": "Fire blight is a bacterial disease that affects apples, pears, and roses. It causes wilting, blackening, and a burnt appearance of branches. Pruning and copper sprays are used for control.",
            "Gray Mold": "Gray mold, caused by Botrytis cinerea, affects strawberries, grapes, and tomatoes. It causes gray, fuzzy growth on fruits and leaves. Proper spacing and fungicides help manage the disease.",
            "White Mold": "White mold, caused by Sclerotinia sclerotiorum, affects beans, lettuce, and sunflowers. It causes white, cottony growth on stems and leaves. Crop rotation and fungicides are effective.",
            "Southern Blight": "Southern blight is a fungal disease that affects tomatoes, peppers, and peanuts. It causes wilting and white fungal growth at the base of plants. Soil solarization and fungicides are used for control.",
            "Bacterial Spot": "Bacterial spot affects crops like tomatoes and peppers, causing small, dark lesions on leaves and fruits. Copper sprays and resistant varieties are commonly used for management.",
            "Alternaria Leaf Spot": "Alternaria leaf spot is a fungal disease that affects tomatoes, potatoes, and carrots. It causes dark, concentric spots on leaves. Fungicides and crop rotation help control the disease.",
            "Phytophthora Blight": "Phytophthora blight affects crops like peppers, squash, and cucumbers. It causes wilting, dark lesions, and fruit rot. Well-drained soil and fungicides are essential for control.",
            "Ergot": "Ergot is a fungal disease that affects rye and wheat, causing dark, elongated sclerotia in place of grains. Resistant varieties and crop rotation are key to management.",
            "Take-All": "Take-all is a fungal disease that affects wheat and barley, causing root rot and stunted growth. Crop rotation and fungicides are used for control.",
            "Septoria Leaf Spot": "Septoria leaf spot is a fungal disease that affects tomatoes and wheat. It causes small, dark spots with light centers on leaves. Fungicides and proper sanitation are effective.",
            "Cercospora Leaf Spot": "Cercospora leaf spot affects crops like beets, spinach, and peanuts. It causes circular, tan spots with dark borders on leaves. Fungicides and resistant varieties help manage the disease.",
            "Tar Spot": "Tar spot is a fungal disease that affects corn, causing black, tar-like spots on leaves. Resistant varieties and fungicides are used for control.",
            "Bacterial Canker": "Bacterial canker affects tomatoes and stone fruits, causing wilting, gumming, and cankers on stems. Copper sprays and pruning are effective control measures.",
            "Brown Spot": "Brown spot is a fungal disease that affects rice, causing brown lesions on leaves and grains. Resistant varieties and fungicides are used for management.",
            "Charcoal Rot": "Charcoal rot is a fungal disease that affects soybeans and sorghum, causing wilting and blackened roots. Crop rotation and resistant varieties are key to control.",
            "Crown Gall": "Crown gall is a bacterial disease that affects grapes, roses, and stone fruits. It causes swollen, tumor-like growths on roots and stems. Avoiding wounding plants is crucial for prevention.",
            "Dollar Spot": "Dollar spot is a fungal disease that affects turfgrass, causing small, circular, straw-colored patches. Proper watering and fungicides help manage the disease.",
            "Gummy Stem Blight": "Gummy stem blight is a fungal disease that affects cucumbers and melons. It causes wilting, stem cankers, and gummy exudates. Fungicides and crop rotation are effective.",
            "Leaf Scorch": "Leaf scorch is a bacterial disease that affects almonds, grapes, and blueberries. It causes browning and curling of leaf edges. Controlling insect vectors is essential.",
            "Nematode Infestation": "Nematodes are microscopic worms that infect roots of crops like tomatoes, potatoes, and soybeans. They cause stunted growth and root galls. Crop rotation and nematicides are used for control.",
            "Peach Leaf Curl": "Peach leaf curl is a fungal disease that affects peaches and nectarines. It causes red, curled, and distorted leaves. Fungicides applied during dormancy are effective.",
            "Pythium Root Rot": "Pythium root rot is a fungal disease that affects seedlings and young plants, causing wilting and root decay. Well-drained soil and fungicides are essential for control.",
            "Rhizoctonia Root Rot": "Rhizoctonia root rot affects crops like beans, potatoes, and corn. It causes brown lesions on roots and stems. Crop rotation and fungicides are used for management.",
            "Ring Spot": "Ring spot is a viral disease that affects brassicas and ornamentals. It causes circular, yellow or brown spots on leaves. Controlling aphids and using virus-free seeds are key.",
            "Sooty Mold": "Sooty mold is a fungal growth that appears on leaves and stems of crops like citrus and mangoes. It grows on honeydew secreted by insects. Controlling insect pests is essential.",
            "Stem Rust": "Stem rust is a fungal disease that affects wheat and barley. It causes reddish-brown pustules on stems and leaves. Resistant varieties and fungicides are used for control.",
            "Tomato Spotted Wilt Virus": "Tomato spotted wilt virus affects tomatoes, peppers, and peanuts. It causes ring spots, wilting, and stunted growth. Controlling thrips and using resistant varieties are effective.",
            "Wilt": "Wilt is a fungal disease caused by Fusarium or Verticillium species. It affects crops like tomatoes, cucumbers, and bananas, causing yellowing and wilting. Resistant varieties and crop rotation are recommended.",
            "Yellow Dwarf": "Yellow dwarf is a viral disease that affects barley and wheat. It causes stunted growth and yellowing of leaves. Controlling aphids and using resistant varieties are key.",
            "Zonate Leaf Spot": "Zonate leaf spot is a fungal disease that affects crops like soybeans and peanuts. It causes circular, target-like spots on leaves. Fungicides and crop rotation help manage the disease."
        }
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        
        for item in self.disease_info.keys():
            list_item = OneLineListItem(text=item, on_press=lambda x=item: self.show_disease_info(x))
            self.ids['disease_list'].add_widget(list_item)

    def populate_disease_list(self):
        diseases = list(self.disease_info.keys())
        disease_list = self.ids.disease_list
        disease_list.clear_widgets()
        for disease in diseases:
            item = OneLineListItem(text=disease, on_press=lambda x=disease: self.show_disease_info(x.text))
            disease_list.add_widget(item)

    def search_disease(self):
        query = self.ids.search_field.text.lower()
        disease_list = self.ids.disease_list

        for item in disease_list.children:
            if query in item.text.lower():
                item.opacity = 1
                item.disabled = False
            else:
                item.opacity = 0
                item.disabled = True

    def show_disease_info(self, disease):
        info = self.disease_info.get(disease.text, "No information available.")
        self.dialog = MDDialog(
            title=disease.text,
            text=info,
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def add_new_disease(self):
        self.dialog = MDDialog(
            title="Add New Disease",
            text="Enter the name of the new disease:",
            type="custom",
            content_cls=MDTextField(hint_text="Disease Name"),
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="SAVE", on_release=lambda x: self.save_new_disease())
            ]
        )
        self.dialog.open()
    def save_new_disease(self):
        new_disease = self.dialog.content_cls.text
        if new_disease:
            disease_list = self.ids.disease_list
            item = OneLineListItem(text=new_disease, on_release=lambda x, d=new_disease: self.show_disease_info(d))
            disease_list.add_widget(item)
            self.disease_info[new_disease] = "No information available."  # Default info for new disease
        self.dialog.dismiss()

    def go_back(self):
        self.manager.current = SCREEN_TRACKER[-2] if len(SCREEN_TRACKER) > 1 else 'home'
        SCREEN_TRACKER.pop()

class AlertScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.dialog = None
        self.df = pd.read_excel('assets/data/alert.xlsx')
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        
        for index, row in self.df.iterrows():
            if index and row.items():
                self.ids.alert_list.add_widget(
                    TwoLineIconListItem(
                        IconLeftWidget(
                            icon= row['Icon']
                        ),
                        text=row['Disease'],
                        secondary_text =str(row['Details']),
                        on_press=lambda x=row['Disease'], y = row['Details'], z = row['Solutions']: self.show_details(x, y, z)
                    )
                )
    def show_details(self, title, details, solutions):
        self.dialog = None
        if not self.dialog:
            self.dialog = MDDialog(
            title=str(title.text),
            text=str(details + " \n\n[b][size=20]     Solutions :[/size][/b] \n\n"+solutions),
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()
        
    def close_dialog(self):
        self.dialog.dismiss()
        
    def show_error(self, message, detailed_message=""):
        self.ids.error_message.text = message
        self.ids.detailed_error.text = detailed_message
        self.ids.progress_bar.opacity = 0 
        self.ids.retry_button.disabled = False

    def retry_action(self):
        self.ids.progress_bar.opacity = 1 
        self.ids.retry_button.disabled = True
        self.simulate_retry()

    def simulate_retry(self):
        import time
        time.sleep(2)
        self.show_error("Retry failed. Please check your physical device connection.", "Error Code: 500")

class SelectCrop(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.data=pd.read_excel('assets/data/crop_icons.xlsx')

    def on_enter(self):
        self.ids.cropCollections.clear_widgets()
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.spinner.active = True
        for index, row in self.data.iterrows():
            if index and row.items() :
                self.ids.cropCollections.add_widget(CropCard(cropName=row['Crop Name'],cropIcon=row['Crop Icon']))
        self.ids.spinner.active = False
        
    def on_search_text(self, text):
        def perform_search():
            for index, row in self.data.iterrows():
                if index and row.items():
                    if text.lower() in row['Crop Name'].lower():
                        self.ids['crop_box'].height = 1
                        self.ids.crop_box_results.add_widget(
                            OneLineListItem(text=row['Crop Name'], on_press=lambda x=row['Crop Name']: self.selected_data(x.text))
                        )
        search_thread = threading.Thread(target=perform_search)
        search_thread.start()

    def selected_data(self, text):
        self.ids['search_crop'].text = text
        self.ids['crop_box'].height = 1
    
class CropCard(MDCard, ButtonBehavior):
        def __init__(self,cropName="", cropIcon="", **kwargs):
            super().__init__(**kwargs)
            self.orientation = "vertical"
            self.size_hint_y = None
            self.cropName=cropName
            self.height = dp(100)
            self.ripple_behavior = True
            self.md_bg_color = [0.6,0.6,0.6,0.2]
            
            self.bind(on_press=self.on_press_action)
            icon = MDIconButton(icon=cropIcon, halign="center")
            self.add_widget(icon)

            label = MDLabel(text=cropName, halign="center")
            self.add_widget(label)

        def on_press_action(self,*args,**kargs):
            app = MDApp.get_running_app()
            app.root.ids.screen_manager.current = "CropDetails"
            app.root.ids.screen_manager.get_screen('CropDetails').current_crop = self.cropName

class CropDetails(MDScreen):
    current_crop =""
    current_crop_url=""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = ""
    
    def on_enter(self, *args):
        self.ids.spinner.active = True
        global SCREEN_TRACKER
        if self.manager.current not in SCREEN_TRACKER:
            SCREEN_TRACKER.append(self.manager.current)

        threading.Thread(target=self.get_url, daemon=True).start()

    def get_url(self):
        excel = pd.read_excel("assets/data/crops_and_horticulture.xlsx")
        for index, row in excel.iterrows():
            if self.current_crop == row['Crop']:
                self.current_crop_url= CROP_BASE_URL+row['Link']
                Clock.schedule_once(lambda dt: self.fetch_and_display_data(),0)
                return

    def fetch_and_display_data(self):
        try:
            self.ids.info.clear_widgets()
            response = requests.get(self.current_crop_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string

                paragraphs = soup.find_all('article')
                self.text = ""
                self.ids['info'].add_widget(
                    MDLabel(
                        text=title,
                        font_style="H6",
                        font_size=20,
                        halign= "left",
                        bold= True
                    )
                )
                self.ids.spinner.active = False
                for paragraph in paragraphs:
                    self.text += paragraph.get_text()+"\n"
                    self.ids['info'].add_widget(
                        MDTextField(
                            text=paragraph.get_text(),
                            readonly=True,
                            multiline=True,
                            background_normal='', 
                            background_active='',
                            foreground_color=( 1, 0, 0, 1),
                            background_color=(1, 0, 1, 0),
                        )
                    )
                # self.update_label(title,self.text)
                
            else:
                print(f"Error: Unable to fetch data. Status code: {response.status_code}")
                self.update_label("Failed to fetch data. Please try again later.","")
        except Exception as e:
            print(f"Error 649: {e}")
            self.update_label("An error occurred while fetching data\n Server is not responding..","")


    def update_label(self, title, text):
        Clock.schedule_once(lambda dt: self._update_label_text(title, text=""))

    def _update_label_text(self,title, text=""):
        self.ids.spinner.active = False
        self.ids['info'].add_widget(
            MDLabel(
                text=title,
                font_style="H6",
                font_size=20,
                halign= "left",
                bold= True
            )
        )
        self.ids['info'].add_widget(
            MDTextField(
                text=text,
                readonly=True,
                multiline=True,
                background_normal='', 
                background_active='',
                foreground_color=( 1, 0, 0, 1),
                background_color=(1, 0, 1, 0),
            )
        )
        Animation(opacity=0, duration=0.5).start(self.ids.info)
        Animation(opacity=1, duration=0.5).start(self.ids.info)
    
    def on_read_more(self, *args):
        print("Redirecting to more information...")

class WeatherInfo(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.data_table = None
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None

    def on_start(self):
        self.refresh_weather()

    def refresh_weather(self):
        threading.Thread(target=self.get_current_city(), daemon=True).start()

    def get_current_city(self):
        try:
            ip_info_url = "http://ipinfo.io/json"
            response = requests.get(ip_info_url)
            if response.status_code == 200:
                data = response.json()
                city = data.get("city")
                if city:
                    weather_data = self.get_weather("3a4ef7110e036cd5c66f002cd3e239a2", city)
                    threading.Thread(target=self.display_weather(weather_data))
            else:
                print("Could not get location info.")
                self.show_dialog("!! Error !!", "Server is not responding......")
                return None
        except Exception as e :
            print("Error ",e)
            self.show_dialog("!! Exception !!", "Server is not responding......")
        

    def get_weather(self, api_key, city):
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric'
        }

        try:
            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                print("Error:", response.status_code, response.json())
                self.show_dialog("!! Error !!", "Server is not responding......")
                return {}
        except Exception as e :
            print("Error ",e)
            self.show_dialog("!! Exception !!", "Someting is wrong \nplease try again later......")

    def display_weather(self, data):
        if data:
            weather_info = {
                "City": data['name'],
                "Coordinates (Lon)": data['coord']['lon'],
                "Coordinates (Lat)": data['coord']['lat'],
                "Temperature (°C)": data['main']['temp'],
                "Feels Like (°C)": data['main']['feels_like'],
                "Weather Condition": data['weather'][0]['description'],
                "Pressure (hPa)": data['main']['pressure'],
                "Humidity (%)": data['main']['humidity'],
                "Visibility (m)": data['visibility'],
                "Wind Speed (m/s)": data['wind']['speed'],
                "Wind Direction (°)": data['wind']['deg'],
                "Cloudiness (%)": data['clouds']['all'],
                "Sunrise": data['sys']['sunrise'],
                "Sunset": data['sys']['sunset'],
                "Country": data['sys']['country'],
            }

            if self.data_table:
                self.ids.table_container.remove_widget(self.data_table)

            self.data_table = MDDataTable(
                rows_num=len(weather_info),
                column_data=[
                    ("Parameter", dp(30)),
                    ("Value", dp(40)),
                ],
                row_data=[(param, str(value)) for param, value in weather_info.items()]
            )
            self.ids.label.text="Weather Information"
            self.ids.table_container.add_widget(self.data_table)   

    def show_dialog(self,tit="Alert!!",txt="..."):
        if self.dialog == None:
            self.dialog = MDDialog(
                title=str(tit),
                text=str(txt),
                buttons=[
                    MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                    on_release=self.close_dialog),
                ]
            )
        self.dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()

class CropRecommendation(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        
    def on_search_text(self, txt,field):
        self.ids[field].height= 200        
        self.xlsx=pd.read_excel("assets/data/crop.xlsx")
        self.data=self.xlsx.groupby("City").apply(lambda x: x.drop_duplicates(subset=['City']))
        content=None
        if field=='location':
            content=self.data['City']
        elif field=='weather_type':
            tl=self.ids.location_field.text
            c=self.data[self.data['City'] == tl]
            cont=c['Weather Type']
            for con in cont:
                content=con.split(",")
        elif field=='soil_type':
            tl=self.ids.location_field.text
            tw=self.ids.weather_type_field.text
            c = self.data[(self.data['City'] == tl)]
            cont=c['Soil Type']
            for con in cont:
                content=con.split(",")
                        
        select_options=field+'_search_results'
        self.ids[select_options].clear_widgets()
        for d in content:
            if txt.lower() in d.lower():
                self.ids[select_options].add_widget(
                    OneLineListItem(text=d,on_press=lambda x=d: self.selected_data(x.text,field,select_options))
                )
    
    def selected_data(self,text,field,select_field):
        if text:
            if field=='location':
                self.ids.weather_type_field.disabled = False
            elif field=='weather_type':
                self.ids.soil_type_field.disabled = False
            elif field=='soil_type':
                self.ids.submit_button.disabled = False
            set_value=field+'_field'
            self.ids[set_value].text=text
            self.ids[select_field].clear_widgets()
            self.ids[field].height= 0
            
    def show_result(self):
        l=self.ids.location_field.text
        w=self.ids.weather_type_field.text
        s=self.ids.soil_type_field.text
        txt=""
        if l and w and s:
            c=self.data[self.data['City'] == l]
            cont=c['Recommended Crops']
            txt+='Sugested Crops are : '
            for i in cont:
                c2=i.split(",")
                for j in c2:
                    txt+=f"{j}, "
            self.ids.result.text=txt              

class SearchScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.data=pd.read_excel('assets/data/crop_icons.xlsx')
        self.cropes = []
        for index, row in self.data.iterrows():
            self.cropes.append(row['Crop Name'])
    
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None      

    def on_search_text(self, text):
        self.ids.search_results.clear_widgets()
        for crop in self.cropes:
            if text.lower() in crop.lower():
                self.ids.search_results.add_widget(
                    OneLineListItem(text=crop, on_press=lambda x=crop: self.selected_data(x.text))
                )
    def selected_data(self, text):
        self.ids['search_field'].text=text
        app = MDApp.get_running_app()
        app.root.ids.screen_manager.current = "CropDetails"
        app.root.ids.screen_manager.get_screen('CropDetails').current_crop = text

class ShoppingScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        Clock.schedule_once(self.list_product, 0)
        
    def list_product(self,*args):
        try:
            global PRODUCT_ID_LIST
            global PRODUCT_TYPE_LIST
            response=requests.post(SHOPPING_URL)
            if response.status_code==200:
                inner_MDBoxLayout = None
                for i in response.json()['data']:
                    if i['product_id'] in PRODUCT_ID_LIST:
                        continue
                    else:
                        PRODUCT_ID_LIST.append(i['product_id'])                        
                        if i['type'] not in PRODUCT_TYPE_LIST:
                            PRODUCT_TYPE_LIST.append(i['type'])
                            outer_MDBoxLayout=MDBoxLayout(
                                orientation="vertical",
                                size_hint_y=None,
                                height=dp(50),
                                padding=dp(10),
                            )
                            outer_MDLabel=MDLabel(
                                text=i['type'],
                                halign="left",
                                font_style="H6",
                            )
                            main_MDScrollView=MDScrollView(
                                size_hint_y=None,
                                height=dp(300),
                                do_scroll_x = True,
                            )
                            inner_MDBoxLayout=MDBoxLayout(
                                id=str(i['product_id']),
                                orientation="horizontal",
                            )
                            outer_MDBoxLayout.add_widget(outer_MDLabel)
                            self.ids.shop.add_widget(outer_MDBoxLayout)                        
                            main_MDScrollView.add_widget(inner_MDBoxLayout)
                            self.ids.shop.add_widget(main_MDScrollView)  
                        
                        inner_main_MDCard=MDCard(
                            size_hint=(None,None),
                            size=(dp(160),dp(290)),
                            md_bg_color=[0.6,0.6,0.6,0.2],
                            padding=(dp(10), dp(10)),
                            orientation='vertical',
                        )                        
                        path=self.create_image(path=i['image'],value=i['type'],id=i['product_id'])
                        inner_Image=AsyncImage(
                            source=f'{path}',
                            allow_stretch=True,
                            keep_ratio=False,
                        )
                        title_MDLabel=MDLabel(
                            text=i['title'],
                            halign="center",
                        )
                        info1_MDLabel=MDLabel(
                            text=i['info1'],
                            halign="center",
                        )
                        info2_MDLabel=MDLabel(
                            text=i['info2'],
                            halign="center",
                        )
                        
                        inner_main_MDCard.add_widget(inner_Image)
                        inner_main_MDCard.add_widget(title_MDLabel)
                        inner_main_MDCard.add_widget(info1_MDLabel)
                        inner_main_MDCard.add_widget(info2_MDLabel)
                        
                        inner_MDBoxLayout.add_widget(inner_main_MDCard)
        except Exception as e :
            print("Error : ",e)
            
    
    def create_image(self,path,value,id="",type='jpg'):
        if path is not None :
            temp_file_name=str(f'Products/{value}_{id}.{type}')
            with open(temp_file_name, "wb") as image_file:
                image_file.write(base64.b64decode(path))
            return temp_file_name
        else:
            return None        

class CreatePostScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None

class ProductDetailScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None

class MarketPriceScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None

class NotificationScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None

class MainSchemeDetailScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.scheme_list.clear_widgets()
        try:
            response=requests.post(SCHEMES_URL)
            if response.status_code==200:
                data=response.json()
                for n,l in enumerate(data['data']):
                    flatbutton=MDFlatButton(id= str(n+1),text=f'{n+1}. {l}',size_hint_y=None,height=60,
                                            on_press=lambda x=l: self.display_details(x.id))
                    self.ids.scheme_list.add_widget(flatbutton)     
        except Exception as e:
            print("Error ",e)
    
    def display_details(self,id):
        global SCHEME_ID
        SCHEME_ID=id
        self.manager.current='schemedetail'
        
class SchemeDetailScreen(MDScreen):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        try:
            global SCHEME_ID
            response=requests.post(SCHEME_DETAIL_URL, data={'id':SCHEME_ID})
            if response.status_code==200:
                data=response.json()
                title = f"[b][color=#008000]{data['data']['title']}[/color][/b]\n\n"
                discription = f"[b]Description:[/b] {data['data']['discription']}\n\n"
                benefits = f"[b]Benefits:[/b] {data['data']['benefit']}\n\n"
                eligibility = f"[b]Eligibility:[/b] {data['data']['eligibility']}\n\n"
                documents = f"[b]Documents Required:[/b] {data['data']['document']}\n\n"
                apply_process = f"[b]How to Apply:[/b] {data['data']['apply_process']}\n\n"
                contact = f"[b]Contact:[/b] {data['data']['contact']}\n\n"
                self.ids.scheme_details_label.text = title + discription + benefits + eligibility + documents + apply_process + contact
                
        except Exception as e:
            print("Error : ",e)
            
class CustomFileChooser(FileChooserIconView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 0.5)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ProfileMainScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.profile_img.source=''
        self.get_profile()
        
    def get_profile(self,*args, **kwargs):
        try:
            try:
                os.remove("Images/profile.jpg")
            except:
                pass
            response = requests.post(PROFILE_URL, data={'CURRENT_USER':CURRENT_USER})
            if response.status_code == 200:
                data=response.json()
                self.ids.name.text=data['data']['username']
                self.ids.email.text=data['data']['email']
                self.ids.mobile.text=data['data']['mobile']
                self.ids.address.text=data['data']['location']
                self.ids.pincode.text=data['data']['pincode']
                if data['data']['profile_image'] is not None:
                    get_image(file_name='Images/profile.jpg',base64_image=data['data']['profile_image'])
                    self.ids.profile_img.source='Images/profile.jpg'
            else:
                print(f"Failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error making the request: {e}")           

class UpdateProfileScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog=None
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        try:
            self.remove_widget(self.file_chooser)
        except:
            pass
        self.ids.profile_img2.source=''
        self.get_profile()
             
    def get_profile(self,*args, **kwargs):
        try:
            response = requests.post(PROFILE_URL, data={'CURRENT_USER':CURRENT_USER})
            if response.status_code == 200:
                data=response.json()
                self.ids.name2.text=data['data']['username']
                self.ids.email2.text=data['data']['email']
                self.ids.mobile2.text=data['data']['mobile']
                self.ids.address2.text=data['data']['location']
                self.ids.pincode2.text=data['data']['pincode']
                if data['data']['profile_image'] is not None:
                    get_image(file_name='Images/profile.jpg',base64_image=data['data']['profile_image'])
                    self.ids.profile_img2.source='Images/profile.jpg'
            else:
                print(f"Failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error making the request: {e}")
            
    def update_profile(self):
        try:
            _email = self.ids.email2.text
            _address = self.ids.address2.text
            _mobile = self.ids.mobile2.text
            _pin = self.ids.pincode2.text
            image=self.ids.profile_img2.source
            _img = decode_base64_image(image_path=image) if image !="" else None
            data={'CURRENT_USER':CURRENT_USER,'email':_email,'mobile':_mobile,'location':_address,
                  'pincode':_pin,'profile_image':_img}
            response=requests.post(UPDATE_PROFILE_URL,data=data)
            if response.status_code == 200:
                data = response.json()
                status=data['status']
                message=data['message']
                self.show_dialog(status=status,message=message)
                self.manager.current='profile_main'
                
            else:
                print(f"Error uploading image: {response.status_code}")
                self.show_dialog(status=response.status_code,message='Error uploading image...')
            
        except Exception as e:
            print("error ",e)
            self.show_dialog(status='Error !!',message=f'Exception : {e}')
            
    def show_dialog(self,status,message):
        if self.dialog is None:
            self.dialog = MDDialog(
                title=str(status),
                text=str(message),
                buttons=[
                    MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                 on_release=self.close_dialog),
                ]
            )
        self.dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()

    def change_photo(self):
        self.file_chooser = CustomFileChooser()
        self.file_chooser.bind(on_submit=self.file_selected)

        self.menu = MDDropdownMenu(
            caller=self.children[0],
            items=[
                {
                    "viewclass": "OneLineListItem",
                    "text": "Choose File",
                    "on_release": lambda x='': self.show_file_chooser(self.file_chooser),
                },
            ],
            width_mult=4,
        )
        self.menu.open()

    def file_selected(self, file_chooser, selection, touch):
        if selection:
            selected_file = selection[0]
            self.ids.profile_img2.source = selected_file
            self.remove_widget(file_chooser)

    def show_file_chooser(self, file_chooser):
        self.menu.dismiss()
        self.add_widget(file_chooser)

class ChatBox(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        
    def send_message(self):
        message_input = self.ids.message_input
        message = message_input.text.strip()
        if message:
            self.add_message(message="You : "+message,pos={'right':1})
            threading.Thread(target=self.generate_ai_msg, args=(message,), daemon=True).start()
    
    def generate_ai_msg(self,msg):
        genai.configure(api_key="AIzaSyB5HRHrGP_EdaEOl_YKgIZKKUwUtJ-ls3c")
        model = genai.GenerativeModel("gemini-1.5-flash")
        input = f"Your name is 'Hero' only. my question is : {msg}"
        response = model.generate_content(input)
        Clock.schedule_once(lambda dt: self.add_message(str(response.text),pos={'left':1}))
    
    def add_message(self,message,pos):
        chat_box = self.ids.chat_box
        chat_scroll = self.ids.chat_scroll
        message = str(message).replace("*", "")
        chat_box.add_widget(
            MDTextField(
                text=message,
                readonly=True,
                multiline=True,
                pos_hint= pos,
                size_hint_x=0.8,
                background_normal='', 
                background_active='',
                background_color=(1, 0, 1, 0),
            )
        )
        self.ids.message_input.text = ""

        chat_scroll.scroll_to(chat_box.children[0])

class Budgeting(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.farm_size = ""
        self.yield_per_acre = ""
        self.selling_price = ""
        self.total_expenses = ""
        self.dialog = None
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
     
    def show_dialog(self,title, msg):
        self.dialog = MDDialog(
            title=title,
            text=msg,
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()
           
    def calculate_budget(self):
        self.farm_size = self.ids.farm_size.text
        self.yield_per_acre = self.ids.yield_per_acre.text
        self.selling_price = self.ids.selling_price.text
        self.total_expenses = self.ids.total_expenses.text

        if self.farm_size == "" or self.yield_per_acre == "" or self.selling_price == "" or self.total_expenses == "":
            self.show_dialog("Error", "Please fill in all fields.")
            return
        
        total_production = float(self.farm_size) * float(self.yield_per_acre)
        total_revenue = total_production * float(self.selling_price)
        net_profit = total_revenue - float(self.total_expenses) 

        self.ids.production_label.text = f"Total Production: {total_production} quintals"
        self.ids.revenue_label.text = f"Total Money Earned (Revenue): ₹{total_revenue:,.2f}"
        if net_profit < 0:
            self.ids.profit_label.color = (1, 0.1, 0.1, 1)
            self.ids.profit_label.text = f"Net Loss: ₹{net_profit:,.2f}"
        else:
            self.ids.profit_label.color = (0.1, 1, 0.1, 1)
            self.ids.production_label.color = (0.1, 1, 0, 1)
            self.ids.profit_label.text = f"Net Profit: ₹{net_profit:,.2f}"

class HelpSupport(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog=None
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.name.text=""
        self.ids.feedback_msg.text=""

    def submit_feedback(self):
        name=self.ids.name.text
        feedback_msg=self.ids.feedback_msg.text
        if name and feedback_msg:
            response=requests.post(FEEDBACK_URL,data={'name':name,'message':feedback_msg})
            if response.status_code==200:
                self.show_dialog("Success", "Your message has been send successfully!") 
                self.manager.current='home'
            else:
                self.show_dialog("Error", "Please fill in all fields.")

    def show_dialog(self, title, message):
        if self.dialog==None:
            self.dialog = MDDialog(
                title=title,
                text=message,
                buttons=[
                        MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                        on_release=self.close_dialog),
                    ]
            )
        self.dialog.open()
    
    def close_dialog(self, obj):
        self.dialog.dismiss()

class Setting(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None

class FeedBack(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog = None
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.name_field.text=""
        self.ids.email_field.text=""
        self.ids.message_field.text=""

    def submit_form(self):
        name = self.ids.name_field.text
        email = self.ids.email_field.text
        message = self.ids.message_field.text

        if name and message:
            response=requests.post(CONTACT_US_URL,data={'name':name,
                                                        'email':email if email else None,
                                                        'message':message})
            if response.status_code==200:
                self.show_dialog("Success", "Your message has been submitted successfully!") 
                self.manager.current='home'
            else:
                self.show_dialog("Error", "Server is not responding...\nPlease try again later.")

    def show_dialog(self, title, message):
        if self.dialog==None:
            self.dialog = MDDialog(
                title=title,
                text=message,
                buttons=[
                        MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                        on_release=self.close_dialog),
                    ]
            )
        self.dialog.open()
    
    def close_dialog(self, obj):
        self.dialog.dismiss()

class ContactUs(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog=None
    
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.name_field.text=""
        self.ids.email_field.text=""
        self.ids.message_field.text=""

    def submit_form(self):
        name = self.ids.name_field.text
        email = self.ids.email_field.text
        message = self.ids.message_field.text

        if name and email and message:
            response=requests.post(CONTACT_US_URL,data={'name':name,'email':email,'message':message})
            if response.status_code==200:
                self.show_dialog("Success", "Your message has been submitted successfully!") 
                self.manager.current='home'
            else:
                self.show_dialog("Error", "Please fill in all fields.")

    def show_dialog(self, title, message):
        if self.dialog==None:
            self.dialog = MDDialog(
                title=title,
                text=message,
                buttons=[
                        MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                        on_release=self.close_dialog),
                    ]
            )
        self.dialog.open()
    
    def close_dialog(self, obj):
        self.dialog.dismiss()

class LegalNotice(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_enter(self):
        global SCREEN_TRACKER
        SCREEN_TRACKER.append(self.manager.current) if self.manager.current not in SCREEN_TRACKER else None
        self.ids.legalnotice_text.text=LEGAL_NOTICE_TEXT

class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.dialog=None
        self.screen_manager = Builder.load_file("kv/app.kv")
        Clock.schedule_once(self.Close_StartUp_Page, 5)
        # self.screen_manager.current='welcome'
        return self.screen_manager
    
    def Close_StartUp_Page(self, time):
        self.screen_manager.current = "login"

    def logout(self):
        CURRENT_USER=None
        if self.dialog is None:
            self.dialog = MDDialog(
                title='Alert !! ',
                text="You are Logged out...",
                buttons=[
                    MDFlatButton(text='OK', text_color=self.theme_cls.primary_color,
                                 on_release=self.close_dialog),
                ]
            )
        self.dialog.open()
    
    def close_dialog(self, obj):
        self.dialog.dismiss()
        global SCREEN_TRACKER
        SCREEN_TRACKER=[]
        self.screen_manager.current='login'

    def open_left_menu(self, instance):
        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"{i}",
                "on_release": lambda x=f"{i}": self.menu_callback(x),
            } for i in ['Dashboard', 'Farming Tools', 'Budgeting', 'Search Crops',
                        'Help & Support', 'Logout']]
        self.menu = MDDropdownMenu(
            caller=instance,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
    
    def open_right_menu(self, instance):
        if instance.icon == "chat":
            self.root.ids.screen_manager.current = 'chat'
            return
        right_menu_items = []
        right_menu_items.extend([
            {
                "viewclass": "OneLineListItem",
                "text": f"{i}",
                "on_release": lambda x=f"{i}": self.menu_callback(x),
            } for i in ['Logout', 'FeedBack', 'Contact Us', 'Legal Notice']
        ])
        self.menu = MDDropdownMenu(
            caller=instance,
            items=right_menu_items,
            width_mult=4,
        )
        self.menu.open()

    def menu_callback(self, item):
        if item=='Dashboard':
            self.root.ids.screen_manager.current='home'
        elif item=='Farming Tools':
            self.root.ids.screen_manager.current='shoppingmain'
        elif item=='Budgeting':
            self.root.ids.screen_manager.current='budget'
        elif item=="Search Crops":
            self.root.ids.screen_manager.current='searchscreen'
        elif item=='Notification':
            self.root.ids.screen_manager.current='notification'
        elif item=='Help & Support':
            self.root.ids.screen_manager.current='helpsupport'
        elif item=='Settings':
            self.root.ids.screen_manager.current="settings"
        elif item=='Logout':
            self.logout()
        elif item == "FeedBack":
             self.root.ids.screen_manager.current = 'feedback'
        elif item=='Contact Us':
            self.root.ids.screen_manager.current='contactus'
        elif item=='Legal Notice':
            self.root.ids.screen_manager.current='legalnotice'
        else:
            print(f"{item} clicked...")
        self.menu.dismiss()

if __name__ == "__main__":
    MainApp().run()
