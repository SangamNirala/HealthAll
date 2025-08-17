# Doctronic.ai Clone - Backend Integration Contracts

## API Endpoints Required

### 1. Consultation Management
```
POST /api/consultations
- Create new consultation session
- Body: { symptoms: string, user_id?: string }
- Response: { consultation_id: string, session_token: string }

GET /api/consultations/{consultation_id}
- Get consultation history
- Response: { messages: Message[], user_info: UserInfo, status: string }

PUT /api/consultations/{consultation_id}
- Update consultation with user info
- Body: { age: number, sex: string, additional_info?: object }
```

### 2. Chat/Messaging
```
POST /api/consultations/{consultation_id}/messages
- Send message in consultation
- Body: { content: string, type: "user" | "ai" }
- Response: { message: Message, ai_response?: Message }

GET /api/consultations/{consultation_id}/messages
- Get all messages in consultation
- Response: { messages: Message[] }
```

### 3. AI Medical Analysis
```
POST /api/medical/analyze
- Analyze symptoms and provide diagnosis
- Body: { symptoms: string, user_info: UserInfo, conversation_history: Message[] }
- Response: { diagnosis: Diagnosis[], recommendations: string[], follow_up_questions: string[] }
```

### 4. Doctor Connection (Future)
```
POST /api/doctors/connect
- Connect user to real doctor
- Body: { consultation_id: string, preferred_specialization?: string }
- Response: { appointment_id: string, doctor_info: Doctor, meeting_url: string }
```

## Data Models

### Message
```javascript
{
  id: string,
  consultation_id: string,
  type: "user" | "ai" | "system",
  content: string,
  timestamp: Date,
  metadata?: {
    diagnosis?: Diagnosis[],
    recommendations?: string[],
    user_info_collected?: boolean
  }
}
```

### Consultation
```javascript
{
  id: string,
  session_token: string,
  initial_symptoms: string,
  user_info: {
    age?: number,
    sex?: "male" | "female",
    additional_info?: object
  },
  status: "active" | "completed" | "requires_doctor",
  created_at: Date,
  updated_at: Date,
  messages: Message[]
}
```

### Diagnosis
```javascript
{
  condition: string,
  probability: number, // 0-100
  description: string,
  symptoms: string[],
  treatment_options: string[],
  urgency_level: "low" | "medium" | "high" | "emergency"
}
```

## Mocked Data to Replace

### Frontend Mock Data (src/mock/mockData.js)
1. **mockConversations** → Replace with API calls to consultation endpoints
2. **mockMedicalResponses** → Replace with AI-powered medical analysis
3. **mockDoctorProfiles** → Replace with real doctor database
4. **mockStats** → Replace with real-time statistics from database

### Mock Functionality to Replace
1. **Symptom Analysis Logic** → Integrate with medical AI (GPT-4/Claude for medical conversations)
2. **Conversation Flow Management** → Backend session management
3. **User Info Collection** → Store in MongoDB with consultation
4. **Diagnosis Generation** → AI-powered medical analysis
5. **Response Timing** → Real AI response times instead of setTimeout

## AI Integration Plan

### Medical AI Configuration
- Use Emergent LLM Key for GPT-4 or Claude
- Specialized medical prompts for:
  - Symptom analysis
  - Follow-up questions
  - Diagnosis generation with probabilities
  - Treatment recommendations
  - Emergency detection

### Safety Measures
- Emergency symptom detection (chest pain, stroke symptoms)
- Disclaimer enforcement ("not a licensed doctor")
- Probability-based diagnosis (never 100% certain)
- Clear recommendations for when to see real doctor

## Frontend Integration Changes

### HomePage.jsx Changes
- Replace symptom submission with API call
- Store consultation_id in React state/context
- Handle API errors gracefully

### ChatInterface.jsx Changes
- Replace mock conversation flow with real API calls
- Implement WebSocket for real-time AI responses
- Store messages in backend instead of local state
- Add session management and persistence

### New Context/Hooks Needed
```javascript
// useConsultation.js
const useConsultation = () => {
  // Manage consultation state, API calls, session
}

// ConsultationContext.js
const ConsultationContext = createContext()
// Provide consultation data across components
```

## Database Schema (MongoDB)

### Collections
1. **consultations** - Main consultation sessions
2. **messages** - Individual chat messages
3. **users** - Anonymous user tracking (optional)
4. **medical_templates** - Common medical response templates
5. **doctors** - Doctor profiles for video consultations

### Indexes
- consultations: session_token, created_at
- messages: consultation_id, timestamp
- Performance optimization for chat history retrieval

## Implementation Priority
1. ✅ Frontend-only with mocks (COMPLETED)
2. 🔄 Basic consultation and messaging APIs
3. 🔄 AI medical analysis integration
4. 🔄 Frontend-backend integration
5. 🔄 Session management and persistence
6. 🔄 Real-time messaging (WebSocket)
7. 🔄 Doctor connection system (future)

## Success Criteria
- Seamless transition from mock to real data
- Real AI medical conversations
- Session persistence across page refreshes
- Professional medical-grade responses
- Emergency symptom detection
- HIPAA-compliant data handling