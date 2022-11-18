#Program to create silexx basket from ONE tlog
#It will access the IGN execution template in google sheets and use that information to create a Silexx basket
#The R2 version creates the basket from only a model trade

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import math
import numpy as np
import app_creds

def make_basket(num_orders):

	

	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
	creds = ServiceAccountCredentials.from_json_keyfile_dict(app_creds.app_creds_dictionary, scope)
	client = gspread.authorize(creds)

	# Find a workbook by name and open the desired sheet with the .worksheet function
	Trade_Dump = client.open("Lotus Execution Template R2").worksheet('Large_TopModel')

	# Extract and create a dataframe
	list_of_hashes = Trade_Dump.get_all_records()
	data = pd.DataFrame(list_of_hashes)

	#open up the workbook containing the tranche information
	tranche_info = client.open('Lotus Execution Template R2').worksheet('top_Lotus_Tranches')
	tranche_info = pd.DataFrame(tranche_info.get_all_records())
	#set the index for this DataFrame to 'Account'
	tranche_info.set_index('Account', inplace=True)
	#extract the number of tranches for the Allocation account
	AC_tranches = int(tranche_info.loc['Allocation', 'Tranches'])





	#### LOOK HERE TO ADJUST THE NUMBER OF ORDERS #####
	#set the number of orders desiered for the whole block
	#num_orders = 5
	
	
	
	
	
	
	#multiplier for main and last order.
	main_orders = math.floor(AC_tranches / num_orders)
	last_order = (AC_tranches % num_orders) + main_orders
	adjust_last = int(last_order / main_orders)


	#multiply the base tranche by the main_orders quantity
	data['Qty'] = data['Qty'] * main_orders

	#duplicate the tlog by the number of orders desired
	copies = []
	count = 1
	while count < num_orders:
		
		copy = data.copy(deep=True)
		copies.append(copy)
		count += 1

	#turn each copy into a df and append to the end of data
	#for the last copy, adjust the quantity to the last_order 
	count = 1
	for i in copies:

		if count < len(copies):
			c = pd.DataFrame(i)
			data = pd.concat([data, c], ignore_index=True)
			count += 1
			
		elif count == len(copies):
			c = pd.DataFrame(i)
			#this next line of code converts a columnn with both numeric and non-numeric values into floats
			c['Qty'] = pd.to_numeric(c['Qty'],errors='coerce')
			c['Qty'] = (c['Qty'] / main_orders) * last_order
			c = c.replace(np.nan, 0, regex=True)
			#convert back to int format
			c['Qty'] = c['Qty'].astype(int)

			data = pd.concat([data, c], ignore_index=True)

	#line of code to get rid of the NaN values in the last order copy and to convert the last copy back into int format
	#data['Qty'] = data['Qty'].fillna('')





	###################### MAKE BAKET FUNCTION STARTS BELOW THIS LINE #########################

	#rename date column
	data.rename(columns = {'Date':'datetime'}, inplace = True)

	#format expiry column as datetime and convert it to read YYMMDD.
	#as an example, 11-29-2019 would read 191129
	data['Expiry'] = pd.to_datetime(data['Expiry'])
	data['Expiry'] = data['Expiry'].dt.strftime('%y%m%d')

	#format 'Qty' column as string
	data['Qty'] = data['Qty'].apply(str)



	#split the Symbol column at the space to seperate out the Symbol (RUT or RUTW) from the garbage date and strike portion.
	def split_symbol():
		
		global sym
		list = [i.split(" ") for i in data['Symbol']]
		sym = pd.DataFrame(list, columns = ['sym', 'date_strike'])


	split_symbol()
	data = pd.concat([data, sym], axis=1, join='inner')



	#get the P or C out of the date_strike column
	CP_list = []
	def CP():
		
		for index,row in data.iterrows():
			if row['date_strike'] is None:
				CP_list.append("")
			elif 'P' in row['date_strike']:
				CP_list.append('P')
			elif 'C' in row['date_strike']:
				CP_list.append('C')
			

			
	CP()
	CP_list = pd.DataFrame(CP_list, columns = ['C/P'])
	data = pd.concat([data, CP_list], axis = 1, join='inner')


	#filter out the strike using the Description column
	strike_list = []
	def find_strike():
		
		for index,row in data.iterrows():
			if row['Trans'] != 'Comment':
				s = row['Description'].split(' ')
				strike_list.append(s[2])
			else:
				strike_list.append('')

	find_strike()
	strike_list = pd.DataFrame(strike_list, columns = ['strike'])
	data = pd.concat([data, strike_list], axis = 1, join='inner')

			
				
	#create the symbol for each leg
	silexx_symbol_list = []
	def make_silex_symbol():

		
		for index,row in data.iterrows():
			
			#identify which rows contain trade information and which rows contain tag information
			if row['Trans'] != 'Comment':
				silexx_symbol_list.append('.' + str(row['sym']) + str(row['Expiry']) + str(row['C/P']) + str(row['strike']))
			else:
				silexx_symbol_list.append("")





	make_silex_symbol()
	silexx_symbol_list = pd.DataFrame(silexx_symbol_list, columns = ['Silexx_Symbol'])
	data = pd.concat([data, silexx_symbol_list], axis=1, join='inner')


	#identify account information from Tag
	account_list = []
	def Find_Account():
		
		for index,row in data.iterrows():
			#slight change from the previous format. Here it says if the transaction column IS A comment.
			if row['Trans'] == 'Comment': 
				tag_split = row['Description'].split('|')
				account_list.append(tag_split[0])
			else:
				account_list.append(tag_split[0])
				
	Find_Account()
	account_list = pd.DataFrame(account_list, columns = ['account'])
	data = pd.concat([data, account_list], axis=1, join='inner')


	#attach tag to each leg
	tag_list = []
	def attach_tag():
		
		for index,row in data.iterrows():
			#slight change from the previous format. Here it says if the transaction column IS A comment.
			if row['Trans'] == 'Comment': 
				current_tag = row['Description']
				tag_list.append(current_tag)
			else:
				tag_list.append(current_tag)
				
	attach_tag()
	tag_list = pd.DataFrame(tag_list, columns = ['Tag'])
	data = pd.concat([data, tag_list], axis = 1, join='inner')



	#create account dictionary and map it to the account column in data
	account_dict = {
		'AC':'5CG00006', 'AB':'AtlasBB', 'AH':'AtlasBSH', 'AL':'AtlasLightspeed', 
		'AE':'AtlasEroom', 'EC':'EmiCummins', 'VG':'ERVirginieAfota', 
		'GB':'GailBuzz', 'JO':'JameyOsborne', 'JT':'JeffThomas', 
		'KO':'Konstantin', 'MA':'MarkTaylorApex', 'MB':'MikeBuzz',
		'RM':'RIRA', 'TM':'TDM', 'TK':'ToddKlump',
		'WK':'U2686770', 'YC':'YukoCummins', 'MG':'ManagedAccounts'
		}

	data.account = data.account.map(account_dict)



			
	#sample code of what the trade selection function will look like.
	#I need to build out a function that creates the nested list 'x' of the ranges between the comments
	#from that list I can then run a 'for i in x' loop to grab all of the trades
	#lastly, by using the len() function, I can send the trade selection to the formatter
	def sample_code():	
		x = [[1,4],[5,7]]
		for i in x:
			start = i[0]
			end = i[1]
			
			#print (data[start:end])
			
			if len(data[start:end]) == 1:
				#write code to format a single leg order
				print ('single leg')
			elif len(data[start:end]) == 2:
				#code to format a 2 leg order
				print ('two legs')
			elif len(data[start:end]) == 3:
				#code to format a 3 leg order
				print ('three legs')
			elif len(data[start:end]) == 4:
				#code to format a four leg order
				print ('four legs')



	#function to identify order groupings
	order_group_list = []
	def order_group():
		 
		for row in data.index:
		
			if data.loc[row,'Trans'] == 'Comment':
				start = int(row) + 1
				order_group_list.append(start)

			
			try:
				if data.loc[int(row) + 1, 'Trans'] == 'Comment':
					end = int(row) + 1
					order_group_list.append(end)
			except:
				end = row + 1
				order_group_list.append(end)
			
			
	order_group()			

	#group the beginning and end together to create a nested list
	#this code creates a nested list from a single list 
	new_order_list = []
	def create_nested_list():
		i = 0
		while i<len(order_group_list):
			new_order_list.append(order_group_list[i:i+2])
			i += 2

	create_nested_list()



	#code to create silexx basket file


	#create basket
	basket_file = open('Lotus_Large_TopModel_Basket.bsk', 'w')
	basket_file.truncate()

	#basket file parameters
	header1 = '<?xml version="1.0"?>'
	header2 = '<Basket>'
	footer = '</Basket>'	

	basket_file.write(header1 + '\n')
	basket_file.write(header2 + '\n')


	for i in new_order_list:
		start = i[0]
		end = i[1]
		
		if len(data[start:end]) == 1:
			for i in (data[start:end].index):
				order = ('  <BasketItem' + ' Type="SingleLeg"' + ' Account=' + '"' + data.loc[i, 'account'] + '"' + ' Symbol=' + '"' + data.loc[i, 'Silexx_Symbol'] + '"' + ' Side=' + '"' +
					data.loc[i, 'Trans'] + '"' + ' Qty=' + '"' + data.loc[i, 'Qty'] + '"' + ' OrdType="Limit"' + ' Price="0"' + ' Route="CBOE"' + ' TIF="DAY"' + ' Tag=' + '"' + data.loc[i, 'Tag'] + '"' + ' />')
				basket_file.write(order + '\n')
		
		
		elif len(data[start:end]) == 2:
			#code to format a 2 leg order
			m = 1
			for i in (data[start:end].index):
				if m < 2:
					order = ('  <BasketItem' + str(' Type="MultiLeg"') + str(' Account=') + '"' + data.loc[i, 'account'] + '"' + ' OrdType="Limit"' + ' Price="0"' + ' Route="CBOE"' + ' TIF="DAY"' + ' LegSymbol1=' + '"' + data.loc[i,'Silexx_Symbol'] + 
						'"' + ' LegSide1=' + '"' + data.loc[i, 'Trans'] + '"' + ' LegQty1=' + '"' + data.loc[i, 'Qty'] + '"' + ' LegSymbol2=' + '"' + data.loc[i+1, 'Silexx_Symbol'] + '"' + 
						' LegSide2=' + '"' + data.loc[i+1, 'Trans'] + '"' + ' LegQty2=' + '"' + data.loc[i+1, 'Qty'] + '"' + ' Tag=' + '"' + data.loc[i, 'Tag'] + '"' + ' />')
					basket_file.write(order + '\n')
					m +=1
				else:
					pass
				
				
				
				
		elif len(data[start:end]) == 3:
			m = 1
			for i in (data[start:end].index):
				if m < 2:
					order = ('  <BasketItem' + str(' Type="MultiLeg"') + str(' Account=') + '"' + data.loc[i, 'account'] + '"' + ' OrdType="Limit"' + ' Price="0"' + ' Route="CBOE"' + ' TIF="DAY"' + ' LegSymbol1=' + '"' + data.loc[i,'Silexx_Symbol'] + 
						'"' + ' LegSide1=' + '"' + data.loc[i, 'Trans'] + '"' + ' LegQty1=' + '"' + data.loc[i, 'Qty'] + '"' + ' LegSymbol2=' + '"' + data.loc[i+1, 'Silexx_Symbol'] + '"' + 
						' LegSide2=' + '"' + data.loc[i+1, 'Trans'] + '"' + ' LegQty2=' + '"' + data.loc[i+1, 'Qty'] + '"' +
						' LegSymbol3=' + '"' + data.loc[i+2, 'Silexx_Symbol'] + '"' + ' LegSide3=' + '"' + data.loc[i+2, 'Trans'] + '"' + ' LegQty3=' + '"' + data.loc[i+2, 'Qty'] + '"' + ' Tag=' + '"' + data.loc[i, 'Tag'] + '"' + ' />')
					basket_file.write(order + '\n')
					m +=1
			
			
		elif len(data[start:end]) == 4:
			m = 1
			for i in (data[start:end].index):
				if m < 2:
					order = ('  <BasketItem' + str(' Type="MultiLeg"') + str(' Account=') + '"' + data.loc[i, 'account'] + '"' + ' OrdType="Limit"' + ' Price="0"' + ' Route="CBOE"' + ' TIF="DAY"' + ' LegSymbol1=' + '"' + data.loc[i,'Silexx_Symbol'] + 
						'"' + ' LegSide1=' + '"' + data.loc[i, 'Trans'] + '"' + ' LegQty1=' + '"' + data.loc[i, 'Qty'] + '"' + ' LegSymbol2=' + '"' + data.loc[i+1, 'Silexx_Symbol'] + '"' + 
						' LegSide2=' + '"' + data.loc[i+1, 'Trans'] + '"' + ' LegQty2=' + '"' + data.loc[i+1, 'Qty'] + '"' +
						' LegSymbol3=' + '"' + data.loc[i+2, 'Silexx_Symbol'] + '"' + ' LegSide3=' + '"' + data.loc[i+2, 'Trans'] + '"' + ' LegQty3=' + '"' + data.loc[i+2, 'Qty'] + '"' + 
						' LegSymbol4=' + '"' + data.loc[i+3, 'Silexx_Symbol'] + '"' + ' LegSide4=' + '"' + data.loc[i+3, 'Trans'] + '"' + ' LegQty4=' + '"' + data.loc[i+3, 'Qty'] + '"' + ' Tag=' + '"' + data.loc[i, 'Tag'] + '"' + ' />')
					basket_file.write(order + '\n')
					m +=1
		
		
	basket_file.write(footer)
	basket_file.close()



	print (data)		
		
def main(num_orders):
	make_basket(num_orders)
		
		
if __name__ == '__main__':

	main(num_orders)		
	



	
		
		



	
	

		


			
























