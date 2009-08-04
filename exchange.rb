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
      head["Content-Type"] = "text/plain"
      
      driver = ExchangeServicePortType.new(@endpoint) 
      #driver.wiredump_dev = STDERR 
      driver.options['protocol.http.auth.ntlm'] = [nil, @username, @password] 
      driver.options["protocol.http.ssl_config.verify_mode"] = nil 
      
      itemShape = ItemResponseShapeType.new(DefaultShapeNamesType.new('Default'))
      distFolderId = DistinguishedFolderIdType.new()
      distFolderId.xmlattr_Id = SOAP::SOAPString.new('contacts')
      parentFolderIds = NonEmptyArrayOfBaseFolderIdsType.new([], [distFolderId])
      
      findItemRequest = FindItemType.new(itemShape, nil, nil, nil, nil, nil, nil, nil, nil, parentFolderIds)
      findItemRequest.xmlattr_Traversal = SOAP::SOAPString.new('Shallow')
      response = driver.findItem(findItemRequest)
      
      out.write "<CiscoIPPhoneDirectory>\n"
      out.write "\t<Title>Directory title goes here</Title>\n" 
      out.write "\t<Prompt>Prompt text goes here</Prompt>\n"
      
      response.responseMessages.findItemResponseMessage[0].rootFolder.items.contact.each do |contact|
        next unless contact.completeName
        next unless contact.phoneNumbers
        next unless contact.phoneNumbers.size > 0
        contact.phoneNumbers.each do |phone|
          next if phone.to_s.empty?
          
          out.write "\t<DirectoryEntry>\n"
          out.write "\t\t<Name>"+ contact.completeName.fullName + "(" + phone.xmlattr_Key + ")" + "</Name>\n"
          out.write "\t\t<Telephone>" + phone + "</Telephone>\n"
          out.write "\t</DirectoryEntry>\n"
        end
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