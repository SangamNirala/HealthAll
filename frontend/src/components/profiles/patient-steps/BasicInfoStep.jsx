import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import FormField from '../../shared/FormField';

const BasicInfoStep = ({ data, onChange, icon: Icon }) => {
  // Ensure data is always an object, handle null/undefined
  const safeData = data || {};
  const updateField = (field, value) => {
    const updatedData = { ...safeData, [field]: value };
    onChange(updatedData);
  };

  const updateNestedField = (parentField, childField, value) => {
    const updatedData = {
      ...safeData,
      [parentField]: {
        ...safeData[parentField],
        [childField]: value
      }
    };
    onChange(updatedData);
  };

  const timezoneOptions = [
    { value: 'America/New_York', label: 'Eastern Time (ET)' },
    { value: 'America/Chicago', label: 'Central Time (CT)' },
    { value: 'America/Denver', label: 'Mountain Time (MT)' },
    { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
    { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
    { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
  ];

  const languageOptions = [
    { value: 'English', label: 'English' },
    { value: 'Spanish', label: 'Español' },
    { value: 'French', label: 'Français' },
    { value: 'German', label: 'Deutsch' },
    { value: 'Italian', label: 'Italiano' },
    { value: 'Portuguese', label: 'Português' },
    { value: 'Chinese', label: '中文' },
    { value: 'Japanese', label: '日本語' },
    { value: 'Korean', label: '한국어' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        {Icon && <Icon className="w-8 h-8 text-blue-500" />}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Basic Information</h2>
          <p className="text-gray-600">Let's start with your essential information</p>
        </div>
      </div>

      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle>Personal Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              type="input"
              label="Full Name"
              value={safeData.full_name || ''}
              onChange={(value) => updateField('full_name', value)}
              placeholder="Enter your full name"
              required
            />

            <FormField
              type="number"
              label="Age"
              value={safeData.age || ''}
              onChange={(value) => updateField('age', parseInt(value) || '')}
              placeholder="Enter your age"
              min="1"
              max="120"
              required
            />

            <FormField
              type="select"
              label="Gender"
              value={safeData.gender || ''}
              onChange={(value) => updateField('gender', value)}
              placeholder="Select your gender"
              options={[
                { value: 'Male', label: 'Male' },
                { value: 'Female', label: 'Female' },
                { value: 'Non-binary', label: 'Non-binary' },
                { value: 'Prefer not to say', label: 'Prefer not to say' },
              ]}
              required
            />

            <FormField
              type="input"
              label="Location"
              value={safeData.location || ''}
              onChange={(value) => updateField('location', value)}
              placeholder="City, State/Country"
              helpText="This helps us provide location-specific health recommendations"
            />

            <FormField
              type="select"
              label="Timezone"
              value={safeData.timezone || ''}
              onChange={(value) => updateField('timezone', value)}
              placeholder="Select your timezone"
              options={timezoneOptions}
              helpText="Used for scheduling reminders and tracking"
            />

            <FormField
              type="select"
              label="Preferred Language"
              value={safeData.preferred_language || ''}
              onChange={(value) => updateField('preferred_language', value)}
              placeholder="Select your language"
              options={languageOptions}
            />
          </div>
        </CardContent>
      </Card>

      {/* Contact Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>Communication Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <FormField
              type="checkbox"
              label="Email notifications"
              value={data.contact_preferences?.email}
              onChange={(value) => updateNestedField('contact_preferences', 'email', value)}
              helpText="Receive health tips, reminders, and updates via email"
            />

            <FormField
              type="checkbox"
              label="SMS notifications"
              value={data.contact_preferences?.sms}
              onChange={(value) => updateNestedField('contact_preferences', 'sms', value)}
              helpText="Get reminders and alerts via text messages"
            />

            <FormField
              type="checkbox"
              label="Push notifications"
              value={data.contact_preferences?.push}
              onChange={(value) => updateNestedField('contact_preferences', 'push', value)}
              helpText="Receive notifications through the mobile app"
            />
          </div>
        </CardContent>
      </Card>

      {/* Emergency Contact */}
      <Card>
        <CardHeader>
          <CardTitle>Emergency Contact (Optional)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              type="input"
              label="Emergency Contact Name"
              value={data.emergency_contact?.name}
              onChange={(value) => updateNestedField('emergency_contact', 'name', value)}
              placeholder="Full name"
            />

            <FormField
              type="tel"
              label="Emergency Contact Phone"
              value={data.emergency_contact?.phone}
              onChange={(value) => updateNestedField('emergency_contact', 'phone', value)}
              placeholder="+1-555-123-4567"
            />

            <FormField
              type="input"
              label="Relationship"
              value={data.emergency_contact?.relationship}
              onChange={(value) => updateNestedField('emergency_contact', 'relationship', value)}
              placeholder="Spouse, Parent, Sibling, etc."
            />

            <FormField
              type="email"
              label="Emergency Contact Email"
              value={data.emergency_contact?.email}
              onChange={(value) => updateNestedField('emergency_contact', 'email', value)}
              placeholder="emergency@example.com"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BasicInfoStep;