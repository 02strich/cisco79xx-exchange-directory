require 'rubygems'
gem 'soap4r'
require 'defaultDriver' 
require 'default'
require 'mongrel'

class ExchangeContactsHandler < Mongrel::HttpHandler
  
  @endpoint = 'http://owa.your-exchange.com/ews/Exchange.asmx'
  @username = 'SAM_account_name'
  @password = 'test123'
  
  def initialize(yml_file)
    config = YAML.load_file(yml_file)
    @endpoint = config['endpoint']
    @username = config['username']
    @password = config['password']
  end
  
  def process(request, response)
    response.start(200) do |head,out|
      page = request.params["REQUEST_PATH"]
      page.slice!(0)
      page = page.to_i

      head["Content-Type"] = "text/xml"
      head["Connection"] = "close"
      head["Expires"] = "-1"
      head["Refresh"] = "0; url=http://192.168.178.15:3000/" + (page+1).to_s
      
      driver = ExchangeServicePortType.new(@endpoint) 
      #driver.wiredump_dev = STDERR 
      driver.options['protocol.http.auth.ntlm'] = [nil, @username, @password] 
      driver.options["protocol.http.ssl_config.verify_mode"] = nil 
      
      itemShape = ItemResponseShapeType.new(DefaultShapeNamesType.new('Default'))
      distFolderId = DistinguishedFolderIdType.new()
      distFolderId.xmlattr_Id = SOAP::SOAPString.new('contacts')
      parentFolderIds = NonEmptyArrayOfBaseFolderIdsType.new([], [distFolderId])
      
      #fieldOrderPath = PathToUnindexedFieldType.new()
      #fieldOrderPath.xmlattr_FieldURI = SOAP::SOAPString.new('contacts:Surname')
      #fieldOrder = FieldOrderType.new(fieldOrderPath)
      #fieldOrder.xmlattr_Order = SOAP::SOAPString.new('Ascending')
      #sortOrder = [fieldOrder]
      
      #findItemRequest = FindItemType.new(itemShape, nil, nil, nil, nil, nil, nil, nil, sortOrder, parentFolderIds)
      findItemRequest = FindItemType.new(itemShape, nil, nil, nil, nil, nil, nil, nil, nil, parentFolderIds)
      findItemRequest.xmlattr_Traversal = SOAP::SOAPString.new('Shallow')
      response = driver.findItem(findItemRequest)
      
      out.write "<CiscoIPPhoneDirectory>\n"
      out.write "\t<Title>Directory title goes here</Title>\n" 
      out.write "\t<Prompt>Prompt text goes here</Prompt>\n"
      
      count = 0
      response.responseMessages.findItemResponseMessage[0].rootFolder.items.contact.each do |contact|
        next unless contact.completeName
        next unless contact.phoneNumbers
        next unless contact.phoneNumbers.size > 0
        contact.phoneNumbers.each do |phone|
          next if phone.to_s.empty?
          
          count += 1 
          next if count < 32*page
		  
		  # normalization
		  phone_number = phone.to_s
		  phone_number.sub!("(","")
		  phone_number.sub!("+","00")
		  phone_number.sub!(" ","")
		  
          out.write "\t<DirectoryEntry>\n"
          out.write "\t\t<Name>"+ contact.completeName.fullName + "(" + phone.xmlattr_Key + ")" + "</Name>\n"
          out.write "\t\t<Telephone>" + phone_number + "</Telephone>\n"
          out.write "\t</DirectoryEntry>\n"

         break if count == 32*(page+1)
        end
        break if count == 32*(page+1)
      end
      
      out.write "</CiscoIPPhoneDirectory>"
    end
  end
end

puts "Starting server on port 3000 ...."
h = Mongrel::HttpServer.new("0.0.0.0", "3000")
h.register("/", ExchangeContactsHandler.new('config.yml'))
#h.register("/files", Mongrel::DirHandler.new("."))
h.run.join
puts "Stopping server"
