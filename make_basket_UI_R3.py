from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import make_basket_Large_Bottom_Model_R3
import make_basket_Large_Top_Model_R3



#import client secret json file for use in executable


#create main window and define geometry
window = Tk()
window.title('Make Basket')
window.geometry('750x275')

#create a tab control
tab_control = ttk.Notebook(window)

#create LTS tab
LTS_Tab = ttk.Frame(tab_control)
tab_control.add(LTS_Tab, text='LTS')
tab_control.pack(expand=1, fill='both')

#write functions for button clicks

def large_top():
	num_orders = large_top_orders.get()
	NE_num_orders = NE_top_orders.get()
	if num_orders != "":
                
		num_orders = int(num_orders)
		NE_num_orders = int(NE_num_orders)
		make_basket_Large_Top_Model_R3.main(num_orders, NE_num_orders)
		messagebox.showinfo('order info', 'Order Created')
             
	else:
		messagebox.showinfo('order info', 'ERROR: Enter number of orders')
			
def large_bottom():
	num_orders = large_bottom_orders.get()
	NE_num_orders = NE_bottom_orders.get()
	
	if num_orders != "":
                
		num_orders = int(num_orders)
		NE_num_orders = int(NE_num_orders)
		make_basket_Large_Bottom_Model_R3.main(num_orders, NE_num_orders)
		messagebox.showinfo('order info', 'Order Created')
             
	else:
		messagebox.showinfo('order info', 'ERROR: Enter number of orders')
	


#create buttons for LTS
large_top_basket = Button(LTS_Tab, text='Large Top Basket', width=17, command=large_top)
large_top_basket.place(x=125, y=20)

large_bottom_basket = Button(LTS_Tab, text='Large Bottom Basket', width=17, command=large_bottom)
large_bottom_basket.place(x=500, y=20)


#create order amount entry field for Blackpier
large_top_text = Label(LTS_Tab, text='Blackpier Orders:')
large_top_text.place(x=125, y=75)
large_top_orders = Entry(LTS_Tab, width=9)
large_top_orders.place(x=225, y=75)

large_bottom_text = Label(LTS_Tab, text='Blackpier Orders:')
large_bottom_text.place(x=500, y=75)
large_bottom_orders = Entry(LTS_Tab, width=9)
large_bottom_orders.place(x=600, y=75)


#create order amount entry field for New Era
NE_top_text = Label(LTS_Tab, text='New Era Orders:')
NE_top_text.place(x=125, y=140)
NE_top_orders = Entry(LTS_Tab, width=9)
NE_top_orders.place(x=225, y=140)

NE_bottom_text = Label(LTS_Tab, text='New Era Orders:')
NE_bottom_text.place(x=500, y=140)
NE_bottom_orders = Entry(LTS_Tab, width=9)
NE_bottom_orders.place(x=600, y=140)

#run window
window.mainloop()



	
	
