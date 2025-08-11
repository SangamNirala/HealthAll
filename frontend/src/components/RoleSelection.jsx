import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { ArrowRight, User, Stethoscope, Users, UserCheck, MessageCircle, Sparkles } from 'lucide-react';

const roleOptions = [
  {
    type: 'patient',
    title: 'Personal Health Tracking',
    description: 'Track your nutrition, monitor health metrics, get AI-powered meal recommendations',
    features: [
      'Food logging with AI recognition',
      'Health metrics tracking',
      'Personalized meal plans',
      'Progress analytics'
    ],
    buttonText: 'Start Personal\nJourney',
    route: '/patient-dashboard',
    icon: User,
    image: 'https://images.unsplash.com/photo-1434494878577-86c23bcb06b9',
    gradientClass: 'gradient-patient',
    bgColor: 'from-blue-500 to-blue-700'
  },
  {
    type: 'provider',
    title: 'Professional Healthcare Portal',
    description: 'Monitor patients, create diet prescriptions, access clinical decision support',
    features: [
      'Patient management',
      'Clinical analytics',
      'Diet prescription tools',
      'Evidence-based recommendations'
    ],
    buttonText: 'Access Professional\nPortal',
    route: '/provider-dashboard',
    icon: Stethoscope,
    image: 'https://images.unsplash.com/photo-1624727828489-a1e03b79bba8',
    gradientClass: 'gradient-provider',
    bgColor: 'from-emerald-500 to-emerald-700'
  },
  {
    type: 'family',
    title: 'Family Health Management',
    description: 'Manage family member\'s health, coordinate care, track multiple profiles',
    features: [
      'Multiple profile management',
      'Family meal planning',
      'Health coordination',
      'Caregiver tools'
    ],
    buttonText: 'Manage Family\nHealth',
    route: '/family-dashboard',
    icon: Users,
    image: 'https://images.unsplash.com/photo-1576765974102-b756026ecee3',
    gradientClass: 'gradient-family',
    bgColor: 'from-amber-500 to-amber-700'
  },
  {
    type: 'guest',
    title: 'Quick Health Tracking',
    description: 'Basic nutrition tracking and health monitoring without account creation',
    features: [
      'Simple food logging',
      'Basic nutrition info',
      'Temporary tracking',
      'No data storage'
    ],
    buttonText: 'Try Guest\nMode',
    route: '/guest-dashboard',
    icon: UserCheck,
    image: 'https://images.unsplash.com/photo-1623658045230-605cb00c80d6',
    gradientClass: 'gradient-guest',
    bgColor: 'from-purple-500 to-purple-700'
  }
];

const RoleCard = ({ role, index }) => {
  const navigate = useNavigate();
  const [showQuickChat, setShowQuickChat] = useState(false);
  const IconComponent = role.icon;

  const handleDashboardClick = () => {
    navigate(role.route);
  };

  const handleProfileClick = () => {
    if (role.type === 'patient') {
      navigate('/patient-profile');
    } else if (role.type === 'provider') {
      navigate('/provider-profile');
    } else if (role.type === 'family') {
      navigate('/family-profile');
    } else if (role.type === 'guest') {
      // For guest, go to guest setup first
      navigate('/guest-setup');
    }
  };

  const handleQuickChatClick = () => {
    setShowQuickChat(true);
  };

  return (
    <Card 
      className={`role-card slide-in-up delay-${(index + 1) * 100} bg-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden group`}
    >
      <div className="relative h-48 overflow-hidden image-overlay">
        <img 
          src={role.image} 
          alt={role.title}
          className="w-full h-full object-cover"
        />
        <div className={`absolute inset-0 bg-gradient-to-br ${role.bgColor} opacity-80 group-hover:opacity-70 transition-opacity duration-300`} />
        <div className="absolute top-4 right-4 z-10">
          <div className="bg-white/20 backdrop-blur-sm rounded-full p-3">
            <IconComponent className="w-6 h-6 text-white" />
          </div>
        </div>
      </div>
      
      <CardContent className="p-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-3">
          {role.title}
        </h3>
        
        <p className="text-gray-600 mb-6 leading-relaxed">
          {role.description}
        </p>
        
        <div className="space-y-3 mb-8">
          {role.features.map((feature, idx) => (
            <div key={idx} className="flex items-center space-x-3">
              <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${role.bgColor}`} />
              <span className="text-sm text-gray-700">{feature}</span>
            </div>
          ))}
        </div>
        
        {/* Action Buttons */}
        <div className="space-y-3">
          {role.type !== 'guest' && (
            <Button 
              onClick={handleProfileClick}
              className={`w-full bg-gradient-to-r ${role.bgColor} hover:shadow-lg hover:shadow-blue-500/25 transition-shadow duration-300 text-white border-0 py-3 px-6 text-sm font-semibold group`}
            >
              <div className="flex items-center justify-center w-full">
                <User className="w-4 h-4 mr-2" />
                <span>Create Profile</span>
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
              </div>
            </Button>
          )}
          
          <Button 
            onClick={handleDashboardClick}
            variant={role.type !== 'guest' ? "outline" : "default"}
            className={`w-full ${role.type === 'guest' 
              ? `bg-gradient-to-r ${role.bgColor} hover:shadow-lg hover:shadow-blue-500/25 transition-shadow duration-300 text-white border-0` 
              : `border-2 hover:bg-gray-50`
            } py-3 px-6 text-sm font-semibold group`}
          >
            <div className="flex items-center justify-center w-full">
              {role.type === 'guest' ? (
                <>
                  <span className="whitespace-pre-line">{role.buttonText}</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
                </>
              ) : (
                <>
                  <span>View Dashboard</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
                </>
              )}
            </div>
          </Button>
          
          {/* Quick Chat Button for Guest Mode */}
          {role.type === 'guest' && (
            <Button 
              onClick={handleQuickChatClick}
              variant="outline"
              className="w-full border-2 border-purple-200 text-purple-700 hover:bg-purple-50 hover:border-purple-300 py-3 px-6 text-sm font-semibold group"
            >
              <div className="flex items-center justify-center w-full">
                <MessageCircle className="w-4 h-4 mr-2" />
                <span>Quick Chat</span>
                <Sparkles className="w-4 h-4 ml-2 group-hover:scale-110 transition-transform duration-200" />
              </div>
            </Button>
          )}
        </div>
        
        {role.type !== 'guest' && (
          <p className="text-xs text-gray-500 text-center mt-3">
            Create a profile first for personalized experience
          </p>
        )}
      </CardContent>
    </Card>
  );
};

const RoleSelection = () => {
  return (
    <div className="min-h-screen gradient-hero">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-2">
                <Stethoscope className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                HealthNutrition Platform
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex items-center justify-center px-6 py-16">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Choose Your Health Journey
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Select your role to access personalized health and nutrition features designed for medical-grade accuracy
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {roleOptions.map((role, index) => (
              <RoleCard key={role.type} role={role} index={index} />
            ))}
          </div>
          
          {/* Trust indicators */}
          <div className="mt-20 text-center">
            <p className="text-gray-500 mb-8">Trusted by healthcare professionals worldwide</p>
            <div className="flex justify-center items-center space-x-12 opacity-60">
              <div className="text-2xl font-bold text-gray-400">HIPAA Compliant</div>
              <div className="text-2xl font-bold text-gray-400">FDA Approved</div>
              <div className="text-2xl font-bold text-gray-400">Medical Grade</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleSelection;