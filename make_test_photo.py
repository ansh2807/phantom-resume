from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw

img = Image.new('RGB', (400, 400), color='#3355AA')
draw = ImageDraw.Draw(img)
draw.text((150, 190), "TEST", fill='white')
img.save('test_photo.jpg')

doc = Document()
doc.add_heading('Test Candidate', 0)
doc.add_paragraph('Email: test@example.com')
doc.add_paragraph('Phone: +15550000000')
doc.add_picture('test_photo.jpg', width=Inches(1.5))
doc.add_heading('Summary', level=1)
doc.add_paragraph('Results-driven professional with 10 years of experience.')
doc.add_heading('Experience', level=1)
doc.add_paragraph('Led engineering team at ACME. Increased revenue by 40% in 2 years.')
doc.save('Test-Resume-With-Photo.docx')
print("created Test-Resume-With-Photo.docx")
