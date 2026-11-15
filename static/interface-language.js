(function () {
  var languageSelect = document.getElementById('source_language');
  if (!languageSelect) return;
  var language = 'en';
  var originalTextNodes = new Map();
  var originalAttributes = [];
  var originalAttributeValues = new WeakMap();
  var activeObserver = null;

  var hindi = {
    'Citizen Profile': 'नागरिक प्रोफ़ाइल',
    'Citizen Solution Priority — Your Voice. Your Priority. Your Solution.': 'सिटिज़न सॉल्यूशन प्राथमिकता — आपकी आवाज़। आपकी प्राथमिकता। आपका समाधान।',
    'Report an Issue — Citizen Solution Priority': 'समस्या दर्ज करें — सिटिज़न सॉल्यूशन प्राथमिकता',
    'My Reports — Citizen Solution Priority': 'मेरी रिपोर्ट — सिटिज़न सॉल्यूशन प्राथमिकता',
    'Track Your Complaint — Citizen Solution Priority': 'अपनी शिकायत ट्रैक करें — सिटिज़न सॉल्यूशन प्राथमिकता',
    'Login — Citizen Solution Priority': 'लॉग इन — सिटिज़न सॉल्यूशन प्राथमिकता',
    'Register — Citizen Solution Priority': 'पंजीकरण — सिटिज़न सॉल्यूशन प्राथमिकता',
    'Citizen Solution Priority': 'सिटिज़न सॉल्यूशन प्राथमिकता',
    'CITIZEN SOLUTION PRIORITY': 'सिटिज़न सॉल्यूशन प्राथमिकता',
    'BBMP CIVIC PORTAL': 'BBMP नागरिक पोर्टल',
    'CITIZEN REGISTRATION': 'नागरिक पंजीकरण',
    'English': 'अंग्रेज़ी',
    'ಕನ್ನಡ (Kannada)': 'कन्नड़ (Kannada)',
    'हिन्दी (Hindi)': 'हिन्दी (Hindi)',
    'தமிழ் (Tamil)': 'तमिल (Tamil)',
    'తెలుగు (Telugu)': 'तेलुगु (Telugu)',
    'മലയാളം (Malayalam)': 'मलयालम (Malayalam)',
    'اردو (Urdu)': 'उर्दू (Urdu)',
    'বাংলা (Bengali)': 'बंगाली (Bengali)',
    'ಕನ್ನಡ (Kannada)': 'ಕನ್ನಡ (Kannada)',
    'हिन्दी (Hindi)': 'हिन्दी (Hindi)',
    'தமிழ் (Tamil)': 'தமிழ் (Tamil)',
    'తెలుగు (Telugu)': 'తెలుగు (Telugu)',
    'മലയാളം (Malayalam)': 'മലയാളം (Malayalam)',
    'اردو (Urdu)': 'اردو (Urdu)',
    'বাংলা (Bengali)': 'বাংলা (Bengali)',
    'Citizen Solution': 'सिटिज़न सॉल्यूशन',
    'Priority': 'प्राथमिकता',
    'Priority Portal': 'प्राथमिकता पोर्टल',
    'Open navigation menu': 'नेविगेशन मेनू खोलें',
    'Close navigation menu': 'नेविगेशन मेनू बंद करें',
    'MAIN NAVIGATION': 'मुख्य नेविगेशन',
    'CIVIC SERVICES': 'नागरिक सेवाएँ',
    'Home': 'होम',
    'Current': 'वर्तमान',
    'About & How It Works': 'परिचय और यह कैसे काम करता है',
    'Report an Issue': 'समस्या दर्ज करें',
    'Report': 'रिपोर्ट',
    'Search & Track Status': 'स्थिति खोजें और ट्रैक करें',
    'My Reports': 'मेरी रिपोर्ट',
    'My Account': 'मेरा खाता',
    'All Reports': 'सभी रिपोर्ट',
    'Authority Desk': 'अधिकारी डेस्क',
    'Staff Portal': 'कर्मचारी पोर्टल',
    'Login': 'लॉग इन',
    'Register': 'पंजीकरण करें',
    'Logout': 'लॉग आउट',
    'Sign out': 'साइन आउट',
    'Citizen Account': 'नागरिक खाता',
    'Municipal Officer': 'नगरपालिका अधिकारी',
    'Authority Desk Active': 'अधिकारी डेस्क सक्रिय',
    '24/7 Civic Helpline:': '24/7 नागरिक हेल्पलाइन:',
    'Enable desktop alerts for new complaints and status updates': 'नई शिकायतों और स्थिति अपडेट के लिए डेस्कटॉप अलर्ट चालू करें',
    'Install': 'इंस्टॉल करें',
    'Better Community': 'बेहतर समुदाय',
    'Brighter Future': 'उज्ज्वल भविष्य',
    'All rights reserved.': 'सर्वाधिकार सुरक्षित।',
    'Current Location': 'वर्तमान स्थान',
    'Not set': 'निर्धारित नहीं',
    'Welcome Back!': 'वापसी पर स्वागत है!',
    'Login to your account to continue and track your complaints.': 'जारी रखने और अपनी शिकायतों को ट्रैक करने के लिए अपने खाते में लॉग इन करें।',
    'Email or Mobile Number': 'ईमेल या मोबाइल नंबर',
    'Password': 'पासवर्ड',
    'Forgot Password?': 'पासवर्ड भूल गए?',
    'Enter your password': 'अपना पासवर्ड दर्ज करें',
    'OR': 'या',
    "Don't have an account?": 'खाता नहीं है?',
    'Authority Staff Sign In': 'अधिकारी कर्मचारी लॉग इन',
    'A cleaner, safer and better community is in your hands.': 'स्वच्छ, सुरक्षित और बेहतर समुदाय आपके हाथों में है।',
    'Create Your Account': 'अपना खाता बनाएँ',
    'Join us to report issues and make your community better.': 'समस्याएँ दर्ज करने और अपने समुदाय को बेहतर बनाने के लिए हमसे जुड़ें।',
    'Full Name': 'पूरा नाम',
    'Username': 'उपयोगकर्ता नाम',
    'Email Address': 'ईमेल पता',
    'Confirm Password': 'पासवर्ड की पुष्टि करें',
    'Already have an account?': 'पहले से खाता है?',
    'Your citizen profile': 'आपकी नागरिक प्रोफ़ाइल',
    'Citizen Profile': 'नागरिक प्रोफ़ाइल',
    'Manage your citizen identity, reporting area, and complaint progress in one place.': 'अपनी नागरिक पहचान, क्षेत्र और शिकायतों की प्रगति एक ही जगह प्रबंधित करें।',
    'Verified Citizen': 'सत्यापित नागरिक',
    'Edit Profile': 'प्रोफ़ाइल संपादित करें',
    'City': 'शहर',
    'Neighborhood': 'पड़ोस',
    'Select your area': 'अपना क्षेत्र चुनें',
    'Ward': 'वार्ड',
    'Full name': 'पूरा नाम',
    'Email address': 'ईमेल पता',
    'Email': 'ईमेल',
    'Select Ward / Area…': 'वार्ड / क्षेत्र चुनें…',
    'Select Ward / Area...': 'वार्ड / क्षेत्र चुनें...',
    'e.g. Near Metro Station, 5th Cross Road': 'जैसे मेट्रो स्टेशन के पास, 5वीं क्रॉस रोड',
    'e.g. Ramesh Kumar': 'जैसे रमेश कुमार',
    'Choose a username': 'उपयोगकर्ता नाम चुनें',
    'At least 10 characters': 'कम से कम 10 अक्षर',
    'Repeat your password': 'अपना पासवर्ड दोबारा लिखें',
    'name@example.com': 'name@example.com',
    'name@example.com or username': 'name@example.com या उपयोगकर्ता नाम',
    'Toggle password visibility': 'पासवर्ड दिखाएँ या छिपाएँ',
    'Toggle confirm password visibility': 'पुष्टि पासवर्ड दिखाएँ या छिपाएँ',
    'Back to home': 'होम पर वापस जाएँ',
    'Back to login': 'लॉग इन पर वापस जाएँ',
    'Back to category selection': 'श्रेणी चयन पर वापस जाएँ',
    'Stronger Communities Together': 'मिलकर सशक्त समुदाय',
    'Preferred language': 'पसंदीदा भाषा',
    'Profile photo': 'प्रोफ़ाइल फोटो',
    'Choose an image or take a photo with your device camera.': 'तस्वीर चुनें या अपने डिवाइस के कैमरे से फोटो लें।',
    'Use camera': 'कैमरा खोलें',
    'Take photo': 'फोटो लें',
    'Cancel camera': 'कैमरा बंद करें',
    'Save Profile': 'प्रोफ़ाइल सहेजें',
    'Your saved area can be used automatically when you report an issue.': 'समस्या दर्ज करते समय आपका सहेजा हुआ क्षेत्र अपने आप इस्तेमाल किया जा सकता है।',
    'My Area / Ward': 'मेरा क्षेत्र / वार्ड',
    'Save your usual location for quicker complaint reporting and local routing.': 'शिकायत जल्दी दर्ज करने और स्थानीय विभाग तक भेजने के लिए अपना सामान्य स्थान सहेजें।',
    'Not set': 'निर्धारित नहीं',
    'Report an issue': 'समस्या दर्ज करें',
    'My Complaints': 'मेरी शिकायतें',
    'See where your reports stand and follow their progress.': 'अपनी रिपोर्ट की स्थिति और प्रगति देखें।',
    'View all': 'सभी देखें',
    'Total': 'कुल',
    'Pending': 'लंबित',
    'In Progress': 'प्रगति पर',
    'Resolved': 'हल हो गया',
    'Settings': 'सेटिंग्स',
    'Manage privacy and account security.': 'गोपनीयता और खाते की सुरक्षा प्रबंधित करें।',
    'Dashboard language': 'डैशबोर्ड की भाषा',
    'Privacy & Security': 'गोपनीयता और सुरक्षा',
    'Your account name and email are used to manage your reports and are not shown on the public complaint list.': 'आपके खाते का नाम और ईमेल रिपोर्ट प्रबंधित करने के लिए उपयोग होते हैं और सार्वजनिक शिकायत सूची में नहीं दिखते।',
    'Current password': 'वर्तमान पासवर्ड',
    'New password': 'नया पासवर्ड',
    'Confirm new password': 'नए पासवर्ड की पुष्टि करें',
    'Change Password': 'पासवर्ड बदलें',
    'Help & Support': 'सहायता और समर्थन',
    'Need help with your account or a civic service?': 'खाते या नागरिक सेवा के लिए सहायता चाहिए?',
    'Citizen Helpline': 'नागरिक हेल्पलाइन',
    'Email Support': 'ईमेल सहायता',
    'Sign Out of Account': 'खाते से साइन आउट करें',
    'Your language preference has been updated.': 'आपकी भाषा प्राथमिकता अपडेट कर दी गई है।',
    'Your profile and area details have been updated.': 'आपकी प्रोफ़ाइल और क्षेत्र की जानकारी अपडेट कर दी गई है।',
    'Camera is ready. Select Take photo when you are ready.': 'कैमरा तैयार है। तैयार होने पर फोटो लें चुनें।',
    'Allow camera access in your browser to take a profile photo.': 'प्रोफ़ाइल फोटो लेने के लिए ब्राउज़र में कैमरे की अनुमति दें।',
    'Wait for the camera preview, then try taking the photo again.': 'कैमरा पूर्वावलोकन आने दें, फिर दोबारा फोटो लें।',
    'The photo could not be captured. Please try again.': 'फोटो नहीं ली जा सकी। कृपया फिर कोशिश करें।',
    'Photo captured. Save your profile to keep it.': 'फोटो ली गई। इसे रखने के लिए प्रोफ़ाइल सहेजें।',
    'Photo selected. Save your profile to keep it.': 'फोटो चुनी गई। इसे रखने के लिए प्रोफ़ाइल सहेजें।',
    'Camera permission was denied. Allow camera access in browser settings or choose a photo file.': 'कैमरे की अनुमति नहीं मिली। ब्राउज़र सेटिंग्स में अनुमति दें या फोटो फ़ाइल चुनें।',
    'No camera was found. Choose a photo file instead.': 'कैमरा नहीं मिला। इसके बजाय फोटो फ़ाइल चुनें।',
    'Camera access is not available in this browser. Choose a photo file instead.': 'इस ब्राउज़र में कैमरा उपलब्ध नहीं है। इसके बजाय फोटो फ़ाइल चुनें।',
    'The camera could not be opened. Choose a photo file instead.': 'कैमरा नहीं खुल सका। इसके बजाय फोटो फ़ाइल चुनें।',
    'Camera closed. You can choose a photo file instead.': 'कैमरा बंद है। आप फोटो फ़ाइल चुन सकते हैं।',
    'Choose a PNG, JPG, JPEG, or WEBP photo.': 'PNG, JPG, JPEG या WEBP फोटो चुनें।',
    'Camera closed. You can choose a photo file instead.': 'कैमरा बंद है। आप फोटो फ़ाइल चुन सकते हैं।',
    'Take a photo with your camera or choose an image file.': 'कैमरे से फोटो लें या तस्वीर की फ़ाइल चुनें।',
    'My Reports': 'मेरी रिपोर्ट',
    'Citizen Activity': 'नागरिक गतिविधि',
    '+ Report an Issue': '+ समस्या दर्ज करें',
    'All Statuses': 'सभी स्थितियाँ',
    'Status:': 'स्थिति:',
    'Search by ID, keyword, or ward area...': 'आईडी, शब्द या वार्ड क्षेत्र से खोजें...',
    'View Details': 'विवरण देखें',
    'No matching reports': 'कोई मेल खाती रिपोर्ट नहीं',
    'Try changing your search terms or status filter.': 'खोज शब्द या स्थिति फ़िल्टर बदलकर देखें।',
    'No reports yet': 'अभी कोई रिपोर्ट नहीं',
    'Report an Issue': 'समस्या दर्ज करें',
    'Select a category to file your complaint': 'शिकायत दर्ज करने के लिए श्रेणी चुनें',
    'Choose complaint category': 'शिकायत की श्रेणी चुनें',
    'Garbage': 'कचरा',
    'Collection': 'संग्रह',
    'Road': 'सड़क',
    'Damage': 'क्षति',
    'Street': 'स्ट्रीट',
    'Lights': 'लाइटें',
    'Water': 'पानी',
    'Issues': 'समस्याएँ',
    'Drainage': 'जल निकासी',
    'Overflow': 'ओवरफ़्लो',
    'Tree &': 'पेड़ और',
    'Plants': 'पौधे',
    'Unauthorized': 'अनधिकृत',
    'Const.': 'निर्माण',
    'Sewage &': 'सीवेज और',
    'Sanitation': 'स्वच्छता',
    'Security &': 'सुरक्षा और',
    'Animals': 'जानवर',
    'Other': 'अन्य',
    'Solid Waste': 'ठोस कचरा',
    'Road Maintenance': 'सड़क रखरखाव',
    'Street Light / Electrical': 'स्ट्रीट लाइट / बिजली',
    'Water Supply': 'जल आपूर्ति',
    'Storm Water Drain': 'वर्षा जल नाली',
    'Parks & Trees': 'पार्क और पेड़',
    'Encroachment': 'अतिक्रमण',
    'Sewage / Sanitation': 'सीवेज / स्वच्छता',
    'Stray Animals': 'आवारा पशु',
    'Others': 'अन्य',
    'Selected Category': 'चुनी हुई श्रेणी',
    'Change': 'बदलें',
    'Describe the issue in detail, landmark, or specific hazard...': 'समस्या, पहचान-चिह्न या विशेष खतरे का विस्तार से वर्णन करें...',
    'Describe the Problem': 'समस्या का विवरण दें',
    'Tap Dictate to speak your complaint in your selected language.': 'चुनी हुई भाषा में शिकायत बोलने के लिए बोलें पर टैप करें।',
    'Dictate': 'बोलकर लिखें',
    'Photo Evidence (Recommended)': 'फोटो प्रमाण (अनुशंसित)',
    'Photo Evidence': 'फोटो प्रमाण',
    'Add a Photo': 'फोटो जोड़ें',
    'Upload evidence photo (JPG, PNG, WebP)': 'प्रमाण की फोटो अपलोड करें (JPG, PNG, WebP)',
    'Allow camera access in your browser to take a complaint photo.': 'शिकायत की फोटो लेने के लिए ब्राउज़र में कैमरे की अनुमति दें।',
    'Photo captured. It will be uploaded with your complaint.': 'फोटो ली गई। यह आपकी शिकायत के साथ अपलोड होगी।',
    'Select Ward / Area…': 'वार्ड / क्षेत्र चुनें…',
    'Area / Ward': 'क्षेत्र / वार्ड',
    'Location / Landmark': 'स्थान / पहचान-चिह्न',
    'Your Name': 'आपका नाम',
    'Receive Status Notifications': 'स्थिति सूचनाएँ प्राप्त करें',
    'Get email updates as authorities review and resolve your grievance.': 'अधिकारियों द्वारा आपकी शिकायत की समीक्षा और समाधान पर ईमेल अपडेट पाएँ।',
    'Use Current Location': 'वर्तमान स्थान का उपयोग करें',
    'GPS attaches precise coordinates for municipal response.': 'नगरपालिका की कार्रवाई के लिए GPS सटीक स्थान जोड़ता है।',
    'Take or choose a photo': 'फोटो लें या चुनें',
    'A similar complaint has already been reported in your area': 'आपके क्षेत्र में इसी तरह की शिकायत पहले ही दर्ज की जा चुकी है',
    'Report and support the existing complaint instead of creating a duplicate. Each report adds one support vote; enough votes raise its priority.': 'नई शिकायत बनाने के बजाय मौजूदा शिकायत का समर्थन करें। हर रिपोर्ट से एक समर्थन वोट जुड़ता है; पर्याप्त वोट मिलने पर प्राथमिकता बढ़ती है।',
    'File a New Complaint': 'नई शिकायत दर्ज करें',
    'Report Existing Complaint': 'मौजूदा शिकायत की रिपोर्ट करें',
    'Already reported': 'पहले ही रिपोर्ट किया गया',
    'Back to Category Selection': 'श्रेणी चयन पर वापस जाएँ',
    'Submit Complaint': 'शिकायत जमा करें',
    'e.g. 518': 'जैसे 518',
    'As entered when filing': 'शिकायत दर्ज करते समय दिया गया',
    'Representative category reference': 'श्रेणी का उदाहरण फोटो',
    'Submitted photo evidence': 'जमा किया गया फोटो प्रमाण',
    'Track Your Complaint': 'अपनी शिकायत ट्रैक करें',
    'Real-Time Civic Tracking': 'नागरिक शिकायत की लाइव ट्रैकिंग',
    'Follow the live investigation and resolution status of your filed issue.': 'अपनी दर्ज समस्या की जाँच और समाधान की स्थिति देखें।',
    'Complaint Number': 'शिकायत संख्या',
    'e.g. #0518': 'जैसे #0518',
    'Search by ID (e.g. #0518), category, area, keyword...': 'आईडी (जैसे #0518), श्रेणी, क्षेत्र या शब्द से खोजें...',
    'Registered Email or Mobile Number': 'पंजीकृत ईमेल या मोबाइल नंबर',
    'Track Complaint': 'शिकायत ट्रैक करें',
    'Filed on': 'दर्ज करने की तारीख',
    'Resolution Progress': 'समाधान की प्रगति',
    'Status Timeline': 'स्थिति क्रम',
    'Complaint Submitted': 'शिकायत जमा की गई',
    'Reviewed': 'समीक्षा की गई',
    'Assigned to Department': 'विभाग को सौंपी गई',
    'Work in Progress': 'काम जारी है',
    'Back to Home': 'होम पर वापस जाएँ',
    'Back to Complaints': 'शिकायतों पर वापस जाएँ',
    'Reported on': 'रिपोर्ट की तारीख',
    'priority': 'प्राथमिकता',
    'Upvote this issue': 'इस समस्या का समर्थन करें',
    'citizen agreed': 'नागरिक सहमत',
    'citizens agreed': 'नागरिक सहमत',
    'Community upvotes help escalate priority for quicker municipal intervention.': 'समुदाय का समर्थन नगरपालिका की त्वरित कार्रवाई के लिए प्राथमिकता बढ़ाने में मदद करता है।',
    'Issue filed and logged in BBMP grievance system.': 'समस्या BBMP शिकायत प्रणाली में दर्ज की गई।',
    'Validated by ward administration desk.': 'वार्ड प्रशासन डेस्क द्वारा सत्यापित।',
    'Dispatched to responsible engineering unit.': 'ज़िम्मेदार इंजीनियरिंग इकाई को भेजी गई।',
    'Field technicians executing site remediation.': 'फील्ड तकनीशियन मौके पर सुधार कार्य कर रहे हैं।',
    'Work verified and completed by municipal officer.': 'नगरपालिका अधिकारी ने कार्य की पुष्टि कर उसे पूरा किया।',
    'No written text was provided; please see submitted photo evidence above.': 'कोई लिखित विवरण नहीं दिया गया; कृपया ऊपर जमा फोटो प्रमाण देखें।',
    'BBMP Docket': 'BBMP शिकायत रिकॉर्ड',
    'Category': 'श्रेणी',
    'Intake Type': 'प्राप्ति का प्रकार',
    'Upvotes': 'समर्थन',
    'Area / Ward': 'क्षेत्र / वार्ड',
    'Landmark': 'पहचान-चिह्न',
    'Citizen Name': 'नागरिक का नाम',
    'Contact Email': 'संपर्क ईमेल',
    'Email Alerts': 'ईमेल सूचनाएँ',
    'GPS Pin': 'GPS स्थान',
    'Open in Map': 'मानचित्र में खोलें',
    'Photo + Text': 'फोटो + विवरण',
    'Subscribed': 'सदस्यता ली गई',
    'Anonymous Citizen': 'गुमनाम नागरिक',
    'Not provided': 'नहीं दिया गया',
    'Not on file': 'रिकॉर्ड में नहीं',
    'No': 'नहीं',
    'Your Voice.': 'आपकी आवाज़।',
    'Your Priority.': 'आपकी प्राथमिकता।',
    'Your Solution.': 'आपका समाधान।',
    'Report civic issues, track their progress, and help build a better community.': 'नागरिक समस्याएँ दर्ज करें, उनकी प्रगति देखें और बेहतर समुदाय बनाने में मदद करें।',
    'How It Works': 'यह कैसे काम करता है',
    'Just a few simple steps to get your issue resolved.': 'समस्या का समाधान पाने के लिए कुछ आसान चरण।',
    'Report an Issue': 'समस्या दर्ज करें',
    'Submit your complaint with proper details.': 'ज़रूरी जानकारी के साथ शिकायत जमा करें।',
    'Track the Complaint': 'शिकायत ट्रैक करें',
    'Check the status and progress anytime.': 'कभी भी स्थिति और प्रगति देखें।',
    'Authorities Review It': 'अधिकारी इसकी समीक्षा करते हैं',
    'Relevant departments review your complaint.': 'संबंधित विभाग आपकी शिकायत की समीक्षा करते हैं।',
    'Get Resolution': 'समाधान पाएँ',
    'Your issue is resolved and you are notified.': 'आपकी समस्या हल होने पर आपको सूचित किया जाएगा।',
    'Priority System': 'प्राथमिकता प्रणाली',
    'High Priority': 'उच्च प्राथमिकता',
    'Medium Priority': 'मध्यम प्राथमिकता',
    'Low Priority': 'कम प्राथमिकता',
    'Key Features': 'मुख्य सुविधाएँ',
    'Everything you need to make your community better.': 'अपने समुदाय को बेहतर बनाने के लिए आपको जो कुछ चाहिए।',
    'Easy Issue Reporting': 'आसानी से समस्या दर्ज करें',
    'Report civic issues in just a few clicks.': 'कुछ ही क्लिक में नागरिक समस्या दर्ज करें।',
    'Complaint Tracking': 'शिकायत ट्रैकिंग',
    'Track your complaint in real time.': 'अपनी शिकायत को तुरंत ट्रैक करें।',
    'Citizen Dashboard': 'नागरिक डैशबोर्ड',
    'View all your complaints in one place.': 'अपनी सभी शिकायतें एक जगह देखें।',
    'Priority-based issue management helps identify and organize important citizen concerns.': 'प्राथमिकता के आधार पर समस्याओं का प्रबंधन ज़रूरी नागरिक मुद्दों को पहचानने और व्यवस्थित करने में मदद करता है।',
    'Urgent issues that need immediate action.': 'तत्काल कार्रवाई की ज़रूरत वाले गंभीर मुद्दे।',
    'Important issues that require timely attention.': 'समय पर ध्यान देने योग्य महत्वपूर्ण मुद्दे।',
    'General issues for planned resolution.': 'नियोजित समाधान के लिए सामान्य मुद्दे।',
    'Learn More': 'और जानें',
    'Cleaner': 'स्वच्छ',
    'Greener': 'हरित',
    'Better': 'बेहतर',
    'Your participation makes a difference. Report, track, and help create a cleaner, safer and better community.': 'आपकी भागीदारी बदलाव लाती है। रिपोर्ट करें, ट्रैक करें और स्वच्छ, सुरक्षित व बेहतर समुदाय बनाने में मदद करें।',
    'Civic issues you report while signed in will appear here with live tracking.': 'लॉग इन रहते हुए दर्ज की गई नागरिक समस्याएँ यहाँ लाइव ट्रैकिंग के साथ दिखेंगी।',
    ' issues reported under your citizen account.': ' समस्याएँ आपके नागरिक खाते से दर्ज की गईं।',
    ' issue reported under your citizen account.': ' समस्या आपके नागरिक खाते से दर्ज की गई।',
    'Showing': 'दिखाए जा रहे हैं',
    'reports': 'रिपोर्ट',
    'Filed on': 'दर्ज किया गया',
    'Description': 'विवरण',
    'Photo Evidence': 'फोटो प्रमाण',
    'English Translation': 'अंग्रेज़ी अनुवाद',
    'Resolution Timeline': 'समाधान का क्रम',
    'No written text was provided; please see submitted photo evidence above.': 'कोई लिखित विवरण नहीं दिया गया; कृपया ऊपर जमा किया गया फोटो प्रमाण देखें।',
    'Search by ID, keyword, or ward area...': 'आईडी, शब्द या वार्ड क्षेत्र से खोजें...',
    'Search by ID (e.g. #0518), category, area, keyword...': 'आईडी (जैसे #0518), श्रेणी, क्षेत्र या शब्द से खोजें...',
    'All (': 'सभी (',
    'upvotes': 'समर्थन',
    'upvote': 'समर्थन',
    'High Priority': 'उच्च प्राथमिकता',
    'Clear Filters': 'फ़िल्टर हटाएँ',
    'Load More Complaints': 'और शिकायतें लोड करें',
    'No complaints match your filters': 'आपके फ़िल्टर से कोई शिकायत मेल नहीं खाती',
    'Try adjusting your search keywords, status filter, or category.': 'खोज शब्द, स्थिति फ़िल्टर या श्रेणी बदलकर देखें।',
    'No complaints filed yet': 'अभी कोई शिकायत दर्ज नहीं हुई',
    'Grievances reported by citizens will appear here.': 'नागरिकों द्वारा दर्ज शिकायतें यहाँ दिखाई देंगी।',
    'Municipal Complaint Registry': 'नगरपालिका शिकायत रजिस्टर',
    'All Complaints': 'सभी शिकायतें',
    'Refresh': 'रीफ़्रेश करें',
    'No matching reports': 'कोई मेल खाती रिपोर्ट नहीं',
    'Showing ': 'दिखाए जा रहे हैं ',
    ' of ': ' में से ',
    ' reports': ' रिपोर्ट',
    'Take a photo with your camera or choose an image file.': 'कैमरे से फोटो लें या तस्वीर की फ़ाइल चुनें।',
    'Allow camera access in your browser to take a profile photo.': 'प्रोफ़ाइल फोटो लेने के लिए अपने ब्राउज़र में कैमरे की अनुमति दें।',
    'Wait for the camera preview, then try taking the photo again.': 'कैमरा पूर्वावलोकन आने दें, फिर दोबारा फोटो लें।',
    'The photo could not be captured. Please try again.': 'फोटो नहीं ली जा सकी। कृपया फिर कोशिश करें।',
    'Your language preference is saved, but the page could not be translated. ': 'आपकी भाषा प्राथमिकता सहेजी गई है, लेकिन पृष्ठ का अनुवाद नहीं हो सका। ',
    'The complaint language is selected, but the form could not be translated. ': 'शिकायत की भाषा चुन ली गई है, लेकिन फ़ॉर्म का अनुवाद नहीं हो सका। ',
    'The translation service returned an incomplete translation.': 'अनुवाद सेवा ने अधूरा अनुवाद दिया।',
    'Together for a Better Community': 'बेहतर समुदाय के लिए साथ मिलकर',
    'Priority (default)': 'प्राथमिकता (डिफ़ॉल्ट)',
    'Newest first': 'सबसे नया पहले',
    'Most upvoted': 'सबसे अधिक समर्थन',
    'Full name': 'पूरा नाम',
    'Email address': 'ईमेल पता',
    'Select Ward / Area...': 'वार्ड / क्षेत्र चुनें...',
    'e.g. Near Metro Station, 5th Cross Road': 'जैसे मेट्रो स्टेशन के पास, 5वीं क्रॉस रोड',
    'e.g. Ramesh Kumar': 'जैसे रमेश कुमार',
    'Choose a username': 'उपयोगकर्ता नाम चुनें',
    'At least 10 characters': 'कम से कम 10 अक्षर',
    'Repeat your password': 'अपना पासवर्ड दोबारा लिखें',
    'name@example.com or username': 'name@example.com या उपयोगकर्ता नाम',
    'Toggle password visibility': 'पासवर्ड दिखाएँ या छिपाएँ',
    'Toggle confirm password visibility': 'पुष्टि पासवर्ड दिखाएँ या छिपाएँ',
    'Back to home': 'होम पर वापस जाएँ',
    'Back to login': 'लॉग इन पर वापस जाएँ',
    'Profile photo preview': 'प्रोफ़ाइल फोटो का पूर्वावलोकन',
    'Selected image preview': 'चुनी गई तस्वीर का पूर्वावलोकन',
    'Email': 'ईमेल',
    'Select Ward / Area…': 'वार्ड / क्षेत्र चुनें…',
    'Solid Waste': 'ठोस कचरा',
    'Road Maintenance': 'सड़क रखरखाव',
    'Street Light / Electrical': 'स्ट्रीट लाइट / बिजली',
    'Water Supply': 'जल आपूर्ति',
    'Storm Water Drain': 'वर्षा जल नाली',
    'Parks & Trees': 'पार्क और पेड़',
    'Encroachment': 'अतिक्रमण',
    'Sewage / Sanitation': 'सीवेज / स्वच्छता',
    'Stray Animals': 'आवारा पशु',
    'Others': 'अन्य',
    'Area / Ward': 'क्षेत्र / वार्ड',
    'Your Name': 'आपका नाम',
    'Receive Status Notifications': 'स्थिति सूचनाएँ प्राप्त करें',
    'Get email updates as authorities review and resolve your grievance.': 'अधिकारियों द्वारा आपकी शिकायत की समीक्षा और समाधान पर ईमेल अपडेट पाएँ।',
    'Use Current Location': 'वर्तमान स्थान का उपयोग करें',
    'GPS attaches precise coordinates for municipal response.': 'नगरपालिका की कार्रवाई के लिए GPS सटीक स्थान जोड़ता है।',
    'A similar complaint has already been reported in your area': 'आपके क्षेत्र में इसी तरह की शिकायत पहले ही दर्ज की जा चुकी है',
    'Report and support the existing complaint instead of creating a duplicate. Each report adds one support vote; enough votes raise its priority.': 'नई शिकायत बनाने के बजाय मौजूदा शिकायत का समर्थन करें। हर रिपोर्ट से एक समर्थन वोट जुड़ता है; पर्याप्त वोट मिलने पर प्राथमिकता बढ़ती है।',
    'File a New Complaint': 'नई शिकायत दर्ज करें',
    'Report Existing Complaint': 'मौजूदा शिकायत की रिपोर्ट करें',
    'Already reported': 'पहले ही रिपोर्ट किया गया',
    'Back to Category Selection': 'श्रेणी चयन पर वापस जाएँ',
    'e.g. 518': 'जैसे 518',
    'As entered when filing': 'शिकायत दर्ज करते समय दिया गया',
    'Reported on': 'रिपोर्ट की तारीख',
    'priority': 'प्राथमिकता',
    'Upvote this issue': 'इस समस्या का समर्थन करें',
    'citizen agreed': 'नागरिक सहमत',
    'citizens agreed': 'नागरिक सहमत',
    'Community upvotes help escalate priority for quicker municipal intervention.': 'समुदाय का समर्थन नगरपालिका की त्वरित कार्रवाई के लिए प्राथमिकता बढ़ाने में मदद करता है।',
    'Issue filed and logged in BBMP grievance system.': 'समस्या BBMP शिकायत प्रणाली में दर्ज की गई।',
    'Validated by ward administration desk.': 'वार्ड प्रशासन डेस्क द्वारा सत्यापित।',
    'Dispatched to responsible engineering unit.': 'ज़िम्मेदार इंजीनियरिंग इकाई को भेजी गई।',
    'Field technicians executing site remediation.': 'फील्ड तकनीशियन मौके पर सुधार कार्य कर रहे हैं।',
    'Work verified and completed by municipal officer.': 'नगरपालिका अधिकारी ने कार्य की पुष्टि कर उसे पूरा किया।',
    'BBMP Docket': 'BBMP शिकायत रिकॉर्ड',
    'Intake Type': 'प्राप्ति का प्रकार',
    'Landmark': 'पहचान-चिह्न',
    'Citizen Name': 'नागरिक का नाम',
    'Contact Email': 'संपर्क ईमेल',
    'Email Alerts': 'ईमेल सूचनाएँ',
    'GPS Pin': 'GPS स्थान',
    'Open in Map': 'मानचित्र में खोलें',
    'Photo + Text': 'फोटो + विवरण',
    'Subscribed': 'सदस्यता ली गई',
    'Anonymous Citizen': 'गुमनाम नागरिक',
    'Not provided': 'नहीं दिया गया',
    'Not on file': 'रिकॉर्ड में नहीं',
    'Everything you need to make your community better.': 'अपने समुदाय को बेहतर बनाने के लिए आपको जो कुछ चाहिए।',
    'Easy Issue Reporting': 'आसानी से समस्या दर्ज करें',
    'Report civic issues in just a few clicks.': 'कुछ ही क्लिक में नागरिक समस्या दर्ज करें।',
    'Priority Management': 'प्राथमिकता प्रबंधन',
    'Organize issues by priority level.': 'समस्याओं को प्राथमिकता के अनुसार व्यवस्थित करें।',
    'Status Updates': 'स्थिति अपडेट',
    'Get real-time updates on your complaint.': 'अपनी शिकायत पर तुरंत अपडेट पाएँ।',
    'Your participation makes a difference. Report, track, and help create a cleaner, safer and better community.': 'आपकी भागीदारी बदलाव लाती है। रिपोर्ट करें, ट्रैक करें और स्वच्छ, सुरक्षित व बेहतर समुदाय बनाने में मदद करें।',
    'Clear Filters': 'फ़िल्टर हटाएँ',
    'Load More Complaints': 'और शिकायतें लोड करें',
    'Try adjusting your search keywords, status filter, or category.': 'खोज शब्द, स्थिति फ़िल्टर या श्रेणी बदलकर देखें।',
    'No complaints filed yet': 'अभी कोई शिकायत दर्ज नहीं हुई',
    'Grievances reported by citizens will appear here.': 'नागरिकों द्वारा दर्ज शिकायतें यहाँ दिखाई देंगी।',
    'Enter your name (up to 80 characters).': 'अपना नाम दर्ज करें (अधिकतम 80 अक्षर)।',
    'Enter a valid email address.': 'मान्य ईमेल पता दर्ज करें।',
    'Choose a password between 10 and 128 characters.': '10 से 128 अक्षरों का पासवर्ड चुनें।',
    'The passwords do not match.': 'पासवर्ड मेल नहीं खाते।',
    'That username or email already has an account. Try signing in.': 'इस उपयोगकर्ता नाम या ईमेल का खाता पहले से है। लॉग इन करने का प्रयास करें।',
    'Your citizen account is ready.': 'आपका नागरिक खाता तैयार है।',
    'Welcome back.': 'वापसी पर स्वागत है।',
    'We could not sign you in with those details.': 'इन विवरणों से लॉग इन नहीं हो सका।',
    'You have signed out.': 'आप साइन आउट हो गए हैं।',
    'City, area, and ward must each be 100 characters or fewer.': 'शहर, क्षेत्र और वार्ड प्रत्येक 100 अक्षरों से कम होने चाहिए।',
    'Choose a supported language.': 'समर्थित भाषा चुनें।',
    'Profile photos must be PNG, JPG, JPEG, or WEBP files.': 'प्रोफ़ाइल फोटो PNG, JPG, JPEG या WEBP फ़ाइल होनी चाहिए।',
    'Choose a valid PNG, JPG, JPEG, or WEBP image for your profile photo.': 'प्रोफ़ाइल फोटो के लिए मान्य PNG, JPG, JPEG या WEBP तस्वीर चुनें।',
    'That email address is already linked to another account.': 'यह ईमेल पता किसी दूसरे खाते से जुड़ा है।',
    'Your current password is incorrect.': 'वर्तमान पासवर्ड गलत है।',
    'The new passwords do not match.': 'नए पासवर्ड मेल नहीं खाते।',
    'Your password has been changed.': 'आपका पासवर्ड बदल दिया गया है।',
    'That profile action is not available.': 'यह प्रोफ़ाइल कार्रवाई उपलब्ध नहीं है।',
    'Please provide a description or upload a photo of the problem.': 'कृपया समस्या का विवरण दें या उसकी फोटो अपलोड करें।',
    'Please choose a valid complaint class.': 'कृपया शिकायत की मान्य श्रेणी चुनें।',
    'Your complaint was filed, but the confirmation email could not be sent.': 'आपकी शिकायत दर्ज हो गई, लेकिन पुष्टि ईमेल नहीं भेजा जा सका।',
    'Email notifications are not configured yet; set the SMTP settings to receive email.': 'ईमेल सूचनाएँ सेट नहीं हैं; ईमेल पाने के लिए SMTP सेटिंग्स करें।',
    'Complaint not found.': 'शिकायत नहीं मिली।',
    'You have already upvoted complaint': 'आप इस शिकायत का पहले ही समर्थन कर चुके हैं',
    'Upvoted complaint': 'शिकायत का समर्थन किया',
    'enough upvotes can bump its priority up.': 'पर्याप्त समर्थन से इसकी प्राथमिकता बढ़ सकती है।',
    'Could not start voice input. Check mic permissions.': 'आवाज़ इनपुट शुरू नहीं हो सका। माइक्रोफ़ोन की अनुमति जाँचें।',
    'Please select a complaint category first.': 'पहले शिकायत की श्रेणी चुनें।',
    'Voice dictation is not supported in this browser. You can type your complaint.': 'इस ब्राउज़र में बोलकर लिखना उपलब्ध नहीं है। आप शिकायत टाइप कर सकते हैं।',
    'Voice dictation stopped.': 'बोलकर लिखना बंद हुआ।',
    'Could not start voice input. Check mic permissions.': 'आवाज़ इनपुट शुरू नहीं हुआ। माइक्रोफ़ोन अनुमति जाँचें।',
    'Geolocation is not supported by your browser.': 'आपका ब्राउज़र स्थान सुविधा का समर्थन नहीं करता।',
    'Detecting current coordinates...': 'वर्तमान स्थान पता किया जा रहा है...',
    'Could not access GPS. You can type the area and landmark.': 'GPS उपलब्ध नहीं है। आप क्षेत्र और पहचान-चिह्न लिख सकते हैं।',
    'Please select a complaint category first.': 'पहले शिकायत की श्रेणी चुनें।'
  };

  function applyHindi() {
  var translatedTextNodes = new WeakMap();

  function translateTextNode(node) {
    if (!node) return;
    var original = originalTextNodes.has(node)
      ? originalTextNodes.get(node)
      : node.nodeValue || '';
    originalTextNodes.set(node, original);
    if (translatedTextNodes.get(node) === node.nodeValue) return;
    if (translatedTextNodes.get(node) === original) return;
    var content = original.trim();
    var translated = hindi[content];
    if (!translated && content.indexOf('Showing ') === 0 && content.indexOf(' reports') !== -1) {
      translated = content
        .replace(/^Showing /, 'दिखाए जा रहे हैं ')
        .replace(/ of /, ' में से ')
        .replace(/ reports?$/, ' रिपोर्ट');
    }
    if (!translated && content.indexOf('View Details') === 0) translated = content.replace('View Details', 'विवरण देखें');
    if (!translated && /^\+\s*\d+\s+upvotes?$/.test(content)) translated = content.replace('upvotes', 'समर्थन').replace('upvote', 'समर्थन');
    if (!translated) {
      var issueSummary = content.match(/^(\d+)\s+(issues?)\s+reported under your citizen account\.$/);
      if (issueSummary) {
        translated = issueSummary[1] + ' ' +
          (issueSummary[2] === 'issue' ? 'समस्या' : 'समस्याएँ') +
          ' आपके नागरिक खाते से दर्ज की गईं।';
      }
    }
    if (!translated && content.indexOf('Listening in ') === 0) {
      translated = content.replace(/^Listening in /, 'सुन रहे हैं: ') + '…';
    }
    if (!translated && content === 'Voice dictation stopped.') {
      translated = 'बोलकर लिखना बंद हुआ।';
    }
    if (!translated && content.indexOf('Voice dictation error (') === 0) {
      translated = content.replace(/^Voice dictation error \(/, 'बोलकर लिखने में त्रुटि (') +
        '। आप शिकायत टाइप कर सकते हैं।';
    }
    if (!translated && content.indexOf('✓ Location acquired (~') === 0) {
      translated = content.replace('✓ Location acquired (~', '✓ स्थान मिला (लगभग ') +
        ' मीटर सटीकता)।';
    }
    if (!translated && content.indexOf('Complaint #') === 0 && content.endsWith(' updated.')) {
      translated = content.replace(/^Complaint #/, 'शिकायत #').replace(/ updated\.$/, ' अपडेट की गई।');
    }
    if (!translated && /^📍\s*/.test(content) && /Ward not specified/.test(content)) {
      translated = content.replace('Ward not specified', 'वार्ड निर्दिष्ट नहीं है');
    }
    if (!translated) return;
    node.nodeValue = original.replace(content, translated);
    translatedTextNodes.set(node, node.nodeValue);
  }

  function translateAttributes(root) {
    var selector = '[placeholder], [title], [aria-label], [alt]';
    var elements = [];
    if (root.nodeType === Node.ELEMENT_NODE && root.matches(selector)) elements.push(root);
    if (root.querySelectorAll) elements = elements.concat(Array.from(root.querySelectorAll(selector)));
    elements.forEach(function (element) {
      ['placeholder', 'title', 'aria-label', 'alt'].forEach(function (attribute) {
        var value = element.getAttribute(attribute);
        if (value && hindi[value]) {
          var savedValues = originalAttributeValues.get(element);
          if (!savedValues) {
            savedValues = {};
            originalAttributeValues.set(element, savedValues);
          }
          if (!Object.prototype.hasOwnProperty.call(savedValues, attribute)) {
            savedValues[attribute] = value;
            originalAttributes.push({ element: element, attribute: attribute, value: value });
          }
          element.setAttribute(attribute, hindi[value]);
        }
      });
    });
  }

  function translateTree(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      translateTextNode(root);
    } else if (root.nodeType === Node.ELEMENT_NODE) {
      var ignoredTags = { SCRIPT: true, STYLE: true, NOSCRIPT: true };
      if (ignoredTags[root.tagName] || root.closest('[data-translation-ignore]')) return;
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      var textNode;
      while ((textNode = walker.nextNode())) translateTextNode(textNode);
      translateAttributes(root);
    }
  }

  if (document.title) {
    var title = originalDocumentTitle.trim();
    var translatedTitle = hindi[title];
    if (!translatedTitle) {
      var titleEnd = ' — Citizen Solution Priority';
      if (title.endsWith(titleEnd)) {
        var titlePrefix = title.slice(0, -titleEnd.length);
        translatedTitle = (hindi[titlePrefix] || titlePrefix) + ' — सिटिज़न सॉल्यूशन प्राथमिकता';
      }
    }
    if (translatedTitle) document.title = translatedTitle;
  }
  translateTree(document.body);

  activeObserver = new MutationObserver(function (records) {
    records.forEach(function (record) {
      record.addedNodes.forEach(translateTree);
      if (record.type === 'characterData') translateTextNode(record.target);
    });
  });
  activeObserver.observe(document.body, { childList: true, characterData: true, subtree: true });
  }

  function translateWithService(targetLanguage) {
    var ignoredTags = { SCRIPT: true, STYLE: true, NOSCRIPT: true, SELECT: true, TEXTAREA: true };
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    var nodes = [];
    var texts = [];
    var seen = Object.create(null);
    var node;

    while ((node = walker.nextNode())) {
      var parent = node.parentElement;
      var content = (node.nodeValue || '').trim();
      if (!content || content.length > 300 || !parent || ignoredTags[parent.tagName]) continue;
      if (parent.closest('[data-translation-ignore], input, textarea, select, script, style, noscript, [contenteditable="true"]')) continue;
      if (!originalTextNodes.has(node)) originalTextNodes.set(node, node.nodeValue);
      nodes.push({ node: node, source: content });
      if (!seen[content]) {
        seen[content] = true;
        texts.push(content);
      }
    }
    if (!texts.length) return;

    var cachePrefix = 'citysolution-ui:' + targetLanguage + ':';
    var translations = Object.create(null);
    var uncachedTexts = [];
    texts.forEach(function (text) {
      try {
        var cached = window.localStorage.getItem(cachePrefix + text);
        if (cached) translations[text] = cached;
        else uncachedTexts.push(text);
      } catch (error) {
        uncachedTexts.push(text);
      }
    });

    function applyTranslations() {
      nodes.forEach(function (entry) {
        var translated = translations[entry.source];
        if (translated) {
          var original = entry.node.nodeValue;
          var start = original.match(/^\s*/)[0];
          var end = original.match(/\s*$/)[0];
          entry.node.nodeValue = start + translated + end;
        }
      });
    }

    function showTranslationError(message) {
      var notice = document.createElement('div');
      notice.className = 'interface-translation-notice';
      notice.setAttribute('role', 'status');
      notice.textContent = message;
      document.body.appendChild(notice);
    }

    if (!uncachedTexts.length) {
      applyTranslations();
      return;
    }
    var batches = [];
    for (var index = 0; index < uncachedTexts.length; index += 100) {
      batches.push(uncachedTexts.slice(index, index + 100));
    }
    Promise.all(batches.map(function (batch) {
      return fetch('/translate-interface', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: targetLanguage, texts: batch })
      }).then(function (response) {
        return response.json().then(function (result) {
          if (!response.ok) throw new Error(result.error || 'Translation is unavailable.');
          return result;
        });
      }).then(function (result) {
        if (!Array.isArray(result.translations) || result.translations.length !== batch.length) {
          throw new Error('The translation service returned an incomplete translation.');
        }
        result.translations.forEach(function (translated, batchIndex) {
          var source = batch[batchIndex];
          if (typeof translated !== 'string' || !translated.trim()) {
            throw new Error('The translation service returned an empty translation.');
          }
          translations[source] = translated;
          try {
            window.localStorage.setItem(cachePrefix + source, translated);
          } catch (error) {
            // Translation still works when browser storage is unavailable.
          }
        });
      });
    })).then(applyTranslations).catch(function (error) {
      showTranslationError(
        'The complaint language is selected, but the form could not be translated. ' +
        error.message
      );
    });
  }

  var originalDocumentTitle = document.title;
  function restoreEnglish() {
    if (activeObserver) {
      activeObserver.disconnect();
      activeObserver = null;
    }
    originalTextNodes.forEach(function (original, node) {
      node.nodeValue = original;
    });
    originalAttributes.forEach(function (entry) {
      if (entry.element.isConnected) {
        entry.element.setAttribute(entry.attribute, entry.value);
      }
    });
    document.title = originalDocumentTitle;
    document.documentElement.lang = 'en';
  }

  function applySelectedLanguage(targetLanguage) {
    restoreEnglish();
    language = targetLanguage;
    document.documentElement.lang = targetLanguage;
    if (targetLanguage === 'en') return Promise.resolve();
    if (targetLanguage === 'hi') {
      applyHindi();
      return Promise.resolve();
    }
    return translateWithService(targetLanguage);
  }

  languageSelect.addEventListener('change', function () {
    var selectedLanguage = languageSelect.value;
    document.querySelectorAll('.interface-translation-notice').forEach(function (notice) {
      notice.remove();
    });
    fetch('/complaint-language', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: selectedLanguage })
    }).then(function (response) {
      return response.json().then(function (result) {
        if (!response.ok) throw new Error(result.error || 'Language selection could not be saved.');
        return applySelectedLanguage(result.language);
      });
    }).catch(function (error) {
      applySelectedLanguage('en');
      var notice = document.createElement('p');
      notice.className = 'interface-translation-notice';
      notice.setAttribute('role', 'status');
      notice.textContent = error.message;
      document.body.appendChild(notice);
    });
  });
})();
