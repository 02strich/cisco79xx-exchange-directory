import suds
from suds.transport.windows import HttpAuthenticated

class CustomTransport(HttpAuthenticated):
	def open(self, request):
		url = request.url
		if url.endswith(".wsdl") or url.endswith(".xsd"):
			return open(url.split('/')[-1])
		else:
			return HttpAuthenticated.open(self, request)
	
	#def send(self, request):
	#	print request
	#	return HttpAuthenticated.send(self, request)

# extract name to show for contact
def get_fullname(contact):
	# get right attribute
	if hasattr(contact, "CompleteName"):
		result = contact.CompleteName.FullName
	elif hasattr(contact, "CompanyName"):
		result = contact.CompanyName
	else:
		result = contact.FileAs
	
	# fix encoding
	result = result.replace(u"\u00e4","ae")
	result = result.replace(u"\u00f6","oe")
	result = result.replace(u"\u00fc","ue")
	result = result.replace(u"\u00c4","Ae")
	result = result.replace(u"\u00d6","Oe")
	result = result.replace("\u00dc","Ue")
	result = result.replace(u'\xe9',"e")
	result = result.replace(u'\xdf',"ss")
	return result

# returns whether this contact has any phone numbers stored
def has_phone_numbers(contact):
	return hasattr(contact, 'PhoneNumbers')

# iterates over all phone numbers for the contact (in normalized form)
def yield_phone_numbers(contact):
	for entry in contact.PhoneNumbers[0]:
		if hasattr(entry, 'value'):
			number = str(entry.value)
			number = number.replace("(","")
			number = number.replace(")","")
			number = number.replace("+","00")
			number = number.replace(" ","")
			yield number

# iterates over all contacts
def yield_all_contacts(client):
	itemShape = client.factory.create('ns1:ItemResponseShapeType')
	itemShape.BaseShape = 'Default'
	
	folder_id = client.factory.create("t:DistinguishedFolderId")
	folder_id._Id = 'contacts'
	parent_folder_ids = client.factory.create("t:NonEmptyArrayOfBaseFolderIdsType")
	parent_folder_ids.DistinguishedFolderId = [folder_id]
	
	response = client.service.FindItem(ItemShape = itemShape, ParentFolderIds = parent_folder_ids, _Traversal = 'Shallow')
	for item in response.FindItemResponse.ResponseMessages.FindItemResponseMessage.RootFolder.Items.Contact:
		yield item

def yield_filtered_contacts(client, first_name=None, last_name=None):
	def create_contains_expression(field_name, field_value):
		field_URI = client.factory.create("t:FieldURI")
		field_URI._FieldURI = field_name
	
		value = client.factory.create("t:ConstantValueType")
		value._Value = field_value
		
		contains_expression = client.factory.create("t:Contains")
		contains_expression._ContainmentComparison = "IgnoreCase"
		contains_expression._ContainmentMode = "Substring"
		contains_expression.Path = field_URI
		contains_expression.Constant = value
		return contains_expression
	
	itemShape = client.factory.create('ns1:ItemResponseShapeType')
	itemShape.BaseShape = 'Default'
	
	folder_id = client.factory.create("t:DistinguishedFolderId")
	folder_id._Id = 'contacts'
	parent_folder_ids = client.factory.create("t:NonEmptyArrayOfBaseFolderIdsType")
	parent_folder_ids.DistinguishedFolderId = [folder_id]
	
	if first_name and last_name:
		and_expression = client.factory.create("t:And")
		and_expression.SearchExpression = [ create_contains_expression("contacts:GivenName", first_name),  create_contains_expression("contacts:Surname", last_name)]
		
		restriction = client.factory.create("t:RestrictionType")
		restriction.SearchExpression = and_expression
	elif first_name:
		restriction = client.factory.create("t:RestrictionType")
		restriction.SearchExpression = create_contains_expression("contacts:GivenName", first_name)
	elif last_name:
		restriction = client.factory.create("t:RestrictionType")
		restriction.SearchExpression = create_contains_expression("contacts:Surname", last_name)
	
	response = client.service.FindItem(ItemShape = itemShape, ParentFolderIds = parent_folder_ids, Restriction = restriction, _Traversal = 'Shallow')
	contacts = response.FindItemResponse.ResponseMessages.FindItemResponseMessage.RootFolder.Items.Contact
	if type(contacts) == list:
		for item in contacts:
			yield item
	else:
		yield contacts

transport = CustomTransport(username='', password='')
client = suds.client.Client('', transport=transport)

#for contact in yield_all_contacts(client):
#for contact in yield_filtered_contacts(client, last_name="Richter"):
for contact in yield_filtered_contacts(client, first_name="Stefan", last_name="Richter"):
	if has_phone_numbers(contact):
		print get_fullname(contact)
		#for number in yield_phone_numbers(contact):
		#	print number