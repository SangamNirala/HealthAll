import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import FormField from '../../shared/FormField';
import { User, Award, Shield } from 'lucide-react';

const ProfessionalIdentityStep = ({ data, onChange, icon: Icon }) => {
  // Ensure data is always an object, handle null/undefined
  const safeData = data || {};
  const updateField = (field, value) => {
    const updatedData = { ...safeData, [field]: value };
    onChange(updatedData);
  };

  const updateRegistrationNumber = (type, value) => {
    const updatedData = {
      ...safeData,
      registration_numbers: {
        ...safeData.registration_numbers,
        [type]: value
      }
    };
    onChange(updatedData);
  };

  const professionalTitles = [
    { value: 'Dr.', label: 'Dr. (Doctor)' },
    { value: 'RD', label: 'RD (Registered Dietitian)' },
    { value: 'RDN', label: 'RDN (Registered Dietitian Nutritionist)' },
    { value: 'MD', label: 'MD (Doctor of Medicine)' },
    { value: 'DO', label: 'DO (Doctor of Osteopathic Medicine)' },
    { value: 'NP', label: 'NP (Nurse Practitioner)' },
    { value: 'PA', label: 'PA (Physician Assistant)' },
    { value: 'CNS', label: 'CNS (Certified Nutrition Specialist)' },
    { value: 'PhD', label: 'PhD (Doctor of Philosophy)' },
    { value: 'MS', label: 'MS (Master of Science)' },
    { value: 'RN', label: 'RN (Registered Nurse)' },
    { value: 'Other', label: 'Other' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        {Icon && <Icon className="w-8 h-8 text-emerald-500" />}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Professional Identity</h2>
          <p className="text-gray-600">Your professional credentials and identification</p>
        </div>
      </div>

      {/* Basic Professional Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="w-5 h-5 mr-2" />
            Basic Professional Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              type="input"
              label="Full Name"
              value={safeData.full_name || ''}
              onChange={(value) => updateField('full_name', value)}
              placeholder="Dr. Jane Smith"
              required
              helpText="Your full legal name as it appears on your license"
            />

            <FormField
              type="select"
              label="Professional Title"
              value={safeData.professional_title || ''}
              onChange={(value) => updateField('professional_title', value)}
              placeholder="Select your title"
              options={professionalTitles}
              required
              helpText="Your primary professional designation"
            />

            <FormField
              type="number"
              label="Years of Experience"
              value={safeData.years_experience || ''}
              onChange={(value) => updateField('years_experience', parseInt(value) || '')}
              placeholder="8"
              min="0"
              max="60"
              required
              helpText="Total years in healthcare/nutrition practice"
            />
          </div>
        </CardContent>
      </Card>

      {/* Licensing Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="w-5 h-5 mr-2" />
            Licensing Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FormField
            type="input"
            label="Medical/Professional License Number"
            value={safeData.medical_license || ''}
            onChange={(value) => updateField('medical_license', value)}
            placeholder="e.g., MD123456, RD789012"
            required
            helpText="Your primary professional license number"
          />

          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Additional Registration Numbers</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                type="input"
                label="State License Number"
                value={safeData.registration_numbers?.state_license || ''}
                onChange={(value) => updateRegistrationNumber('state_license', value)}
                placeholder="CA-RD-12345"
                helpText="State-specific license number if applicable"
              />

              <FormField
                type="input"
                label="National Certification Number"
                value={safeData.registration_numbers?.national_cert || ''}
                onChange={(value) => updateRegistrationNumber('national_cert', value)}
                placeholder="CDR-98765"
                helpText="National board certification number"
              />

              <FormField
                type="input"
                label="DEA Number"
                value={safeData.registration_numbers?.dea_number || ''}
                onChange={(value) => updateRegistrationNumber('dea_number', value)}
                placeholder="Only if you prescribe medications"
                helpText="Required only for prescribing practitioners"
              />

              <FormField
                type="input"
                label="NPI Number"
                value={safeData.registration_numbers?.npi_number || ''}
                onChange={(value) => updateRegistrationNumber('npi_number', value)}
                placeholder="1234567890"
                helpText="National Provider Identifier (10 digits)"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Verification Notice */}
      <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
        <div className="flex items-start space-x-3">
          <Award className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-amber-900 mb-2">Credential Verification</h4>
            <p className="text-sm text-amber-800 mb-3">
              All professional credentials will be verified against official registries before your account is fully activated.
              This process typically takes 2-3 business days.
            </p>
            <ul className="text-sm text-amber-700 space-y-1">
              <li>• Medical licenses are verified through state medical boards</li>
              <li>• Dietitian credentials are verified through CDR (Commission on Dietetic Registration)</li>
              <li>• Nursing credentials are verified through state nursing boards</li>
              <li>• Your profile will be marked as "Pending Verification" until complete</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Privacy & Security */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">🔒 Security & Privacy</h4>
        <p className="text-sm text-blue-800">
          Your professional credentials are encrypted and stored securely. This information is used solely for 
          verification purposes and to ensure patient safety. We comply with all healthcare privacy regulations 
          including HIPAA and state-specific requirements.
        </p>
      </div>
    </div>
  );
};

export default ProfessionalIdentityStep;