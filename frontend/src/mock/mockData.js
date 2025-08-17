export const mockConversations = [
  {
    id: 1,
    messages: [
      {
        id: 1,
        type: "user",
        content: "I have been having headaches for the past 3 days",
        timestamp: new Date(),
      },
      {
        id: 2,
        type: "ai",
        content: "I understand you've been experiencing headaches for 3 days. To help provide the most accurate assessment, I'd like to gather some information. What's your age and biological sex?",
        timestamp: new Date(),
      }
    ],
    userInfo: {
      age: "28",
      sex: "female"
    },
    diagnosis: [
      {
        condition: "Tension Headache",
        probability: 65,
        description: "Most common type of headache, often stress-related"
      },
      {
        condition: "Migraine",
        probability: 25,
        description: "Can include nausea, light sensitivity"
      },
      {
        condition: "Dehydration Headache",
        probability: 10,
        description: "Often overlooked, easily treatable"
      }
    ]
  }
];

export const mockMedicalResponses = {
  headache: {
    questions: [
      "When did the headaches start?",
      "How would you rate the pain from 1-10?",
      "Where exactly do you feel the pain?",
      "Any nausea, light sensitivity, or vision changes?"
    ],
    diagnosis: [
      {
        condition: "Tension Headache",
        probability: 65,
        symptoms: ["bilateral pain", "pressing/tightening quality", "mild to moderate intensity"],
        treatment: ["rest", "over-the-counter pain relief", "stress management"]
      },
      {
        condition: "Migraine",
        probability: 25,
        symptoms: ["unilateral pain", "throbbing quality", "moderate to severe intensity"],
        treatment: ["dark quiet room", "prescription medication", "trigger avoidance"]
      }
    ]
  },
  fever: {
    questions: [
      "What's your current temperature?",
      "How long have you had the fever?",
      "Any other symptoms like chills, body aches?",
      "Have you been exposed to anyone sick recently?"
    ],
    diagnosis: [
      {
        condition: "Viral Infection",
        probability: 70,
        symptoms: ["fever", "fatigue", "possible cold symptoms"],
        treatment: ["rest", "fluids", "fever reducers", "monitor symptoms"]
      }
    ]
  }
};

export const mockDoctorProfiles = [
  {
    id: 1,
    name: "Dr. Sarah Johnson",
    specialization: "Internal Medicine",
    image: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=100&h=100&fit=crop&crop=face",
    rating: 4.9,
    consultations: 2847
  },
  {
    id: 2,
    name: "Dr. Michael Chen",
    specialization: "Family Medicine",
    image: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=100&h=100&fit=crop&crop=face",
    rating: 4.8,
    consultations: 3156
  },
  {
    id: 3,
    name: "Dr. Emily Rodriguez",
    specialization: "Emergency Medicine",
    image: "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=100&h=100&fit=crop&crop=face",
    rating: 4.9,
    consultations: 1923
  }
];

export const mockStats = {
  totalConsultations: "13,853,248",
  activeDoctors: 3,
  averageResponseTime: "< 2 minutes",
  satisfactionRate: "98.7%"
};