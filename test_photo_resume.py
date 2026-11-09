from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw

img = Image.new('RGB', (400, 400), '#3355AA')
ImageDraw.Draw(img).text((150, 190), "TEST", fill='white')
img.save('test_photo.jpg')

doc = Document()
doc.add_heading('Synthetic Test', 0)
doc.add_paragraph('Email: test@example.com')
doc.add_paragraph('Phone: +15550000000')
doc.add_picture('test_photo.jpg', width=Inches(1.5))
doc.add_heading('Summary', level=1)
doc.add_paragraph('Professional with 10 years of experience.')
doc.save('test-photo-resume.docx')
print("created test-photo-resume.docx")
