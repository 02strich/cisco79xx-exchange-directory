#!/usr/bin/env python

import config
import ews

import suds
from suds.transport.windows import HttpAuthenticated

from flask import Flask, request
from werkzeug.serving import WSGIRequestHandler

app = Flask(__name__)
app.config.from_object(config)

def generate_directory_xml(contact_list):
	"""
	Generates the XML required to display the phone directory from
	the list of DirectoryEntry instances given as a parameter.
	"""
	
	def inner_generator():
		yield """
<CiscoIPPhoneDirectory>
	<Title>Phone directory</Title>
	<Prompt>Select an entry.</Prompt>"""
		for contact in contact_list:
			if ews.has_phone_numbers(contact):
				for number in ews.yield_phone_numbers(contact):
					yield """
	<DirectoryEntry>
		<Name>%s</Name>
		<Telephone>%s</Telephone>
	</DirectoryEntry>""" % (ews.get_fullname(contact),  number)
		yield "</CiscoIPPhoneDirectory>"
	
	return '\n'.join(list(inner_generator()))


def generate_search_xml():
	"""
	Generates the XML required to display a phone directory search
	page on the Cisco 79xx IP phones.
	"""
	return """
<CiscoIPPhoneInput>
	<Title>Search for an entry</Title>
	<Prompt>Enter a search keyword.</Prompt>
	<URL>http://%s/directory.xml</URL>
	<InputItem>
		<DisplayName>First Name</DisplayName>
		<QueryStringParam>first_name</QueryStringParam>
		<InputFlags></InputFlags>
		<DefaultValue></DefaultValue>
	</InputItem>
	<InputItem>
		<DisplayName>Last Name</DisplayName>
		<QueryStringParam>last_name</QueryStringParam>
		<InputFlags></InputFlags>
		<DefaultValue></DefaultValue>
	</InputItem>
</CiscoIPPhoneInput>
"""% (app.config["SERVER_NAME"])

@app.route("/")
def root():
	return redirect(url_for('index'))

@app.route("/directory.xml")
def index():
	"""
	Serves the phone directory search page and the search results.
	"""
	# We have received the query string, display the results
	if "last_name" in request.args or "first_name" in request.args:
		first_name = request.args["first_name"] if "first_name" in request.args else None
		last_name = request.args["last_name"] if "last_name" in request.args else None
		
		# Get the directory and filter the entries based on the keyword, then sort them
		xml = generate_directory_xml(ews.yield_filtered_contacts(app.client, first_name=first_name, last_name=last_name))
	# If we haven't received the query string, display the search menu
	else:
		xml = generate_search_xml()
	return app.response_class(xml, mimetype='text/xml')

###############################################################################
class CiscoRequestHandler(WSGIRequestHandler):
	wbufsize = -1
	
def main():
	# connect to EWS
	transport = ews.CustomTransport(username=config.USER_NAME, password=config.PASSWORD)
	app.client = suds.client.Client(config.EWS_URL, transport=transport)
	
	# start server
	app.run(host=app.config['SERVER_IFACE'], port=app.config['SERVER_PORT'], request_handler=CiscoRequestHandler)

if __name__ == "__main__":
	main()
