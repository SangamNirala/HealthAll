import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import FormField from '../../shared/FormField';
import { Calculator, TrendingUp } from 'lucide-react';

const PhysicalMetricsStep = ({ data, onChange, icon: Icon }) => {
  // Ensure data is always an object, handle null/undefined
  const safeData = data || {};
  const [bmiInfo, setBmiInfo] = useState({ bmi: null, category: '', color: '' });

  const updateField = (field, value) => {
    const updatedData = { ...safeData, [field]: value };
    
    // Auto-calculate BMI when height and weight are available
    if (field === 'height_cm' || field === 'current_weight_kg') {
      const height = field === 'height_cm' ? value : updatedData.height_cm;
      const weight = field === 'current_weight_kg' ? value : updatedData.current_weight_kg;
      
      if (height && weight) {
        const heightInMeters = height / 100;
        const bmi = (weight / (heightInMeters * heightInMeters)).toFixed(1);
        updatedData.bmi = parseFloat(bmi);
      }
    }
    
    onChange(updatedData);
  };

  const updateMeasurement = (measurement, value) => {
    const updatedData = {
      ...safeData,
      measurements: {
        ...safeData.measurements,
        [measurement]: value
      }
    };
    onChange(updatedData);
  };

  // Calculate BMI category and color
  useEffect(() => {
    if (data.bmi) {
      let category = '';
      let color = '';
      
      if (data.bmi < 18.5) {
        category = 'Underweight';
        color = 'text-blue-600';
      } else if (data.bmi < 25) {
        category = 'Normal weight';
        color = 'text-green-600';
      } else if (data.bmi < 30) {
        category = 'Overweight';
        color = 'text-yellow-600';
      } else {
        category = 'Obese';
        color = 'text-red-600';
      }
      
      setBmiInfo({ bmi: data.bmi, category, color });
    }
  }, [data.bmi]);

  // Unit conversion helpers
  const cmToFeetInches = (cm) => {
    if (!cm) return '';
    const totalInches = cm / 2.54;
    const feet = Math.floor(totalInches / 12);
    const inches = Math.round(totalInches % 12);
    return `${feet}'${inches}"`;
  };

  const kgToLbs = (kg) => {
    if (!kg) return '';
    return `${Math.round(kg * 2.20462)} lbs`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        {Icon && <Icon className="w-8 h-8 text-blue-500" />}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Physical Metrics</h2>
          <p className="text-gray-600">Your body measurements and composition</p>
        </div>
      </div>

      {/* Basic Measurements */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calculator className="w-5 h-5 mr-2" />
            Basic Measurements
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <FormField
                type="number"
                label="Height (cm)"
                value={data.height_cm}
                onChange={(value) => updateField('height_cm', parseFloat(value) || '')}
                placeholder="170"
                step="0.1"
                min="100"
                max="250"
                required
              />
              {data.height_cm && (
                <p className="text-sm text-gray-500 mt-1">
                  {cmToFeetInches(data.height_cm)}
                </p>
              )}
            </div>

            <div>
              <FormField
                type="number"
                label="Current Weight (kg)"
                value={data.current_weight_kg}
                onChange={(value) => updateField('current_weight_kg', parseFloat(value) || '')}
                placeholder="70"
                step="0.1"
                min="20"
                max="300"
                required
              />
              {data.current_weight_kg && (
                <p className="text-sm text-gray-500 mt-1">
                  {kgToLbs(data.current_weight_kg)}
                </p>
              )}
            </div>

            <div>
              <FormField
                type="number"
                label="Goal Weight (kg)"
                value={data.goal_weight_kg}
                onChange={(value) => updateField('goal_weight_kg', parseFloat(value) || '')}
                placeholder="65"
                step="0.1"
                min="20"
                max="300"
                helpText="Optional: What weight would you like to achieve?"
              />
              {data.goal_weight_kg && (
                <p className="text-sm text-gray-500 mt-1">
                  {kgToLbs(data.goal_weight_kg)}
                </p>
              )}
            </div>

            {/* BMI Display */}
            {bmiInfo.bmi && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">BMI:</span>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-gray-900">{bmiInfo.bmi}</div>
                    <div className={`text-sm font-medium ${bmiInfo.color}`}>
                      {bmiInfo.category}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Body Composition (Optional) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Body Composition (Optional)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              type="number"
              label="Body Fat Percentage (%)"
              value={data.body_fat_percentage}
              onChange={(value) => updateField('body_fat_percentage', parseFloat(value) || '')}
              placeholder="15"
              step="0.1"
              min="3"
              max="50"
              helpText="If you know your body fat percentage from a scale or test"
            />

            <FormField
              type="number"
              label="Muscle Mass (kg)"
              value={data.muscle_mass_kg}
              onChange={(value) => updateField('muscle_mass_kg', parseFloat(value) || '')}
              placeholder="25"
              step="0.1"
              min="5"
              max="100"
              helpText="If available from body composition analysis"
            />
          </div>
        </CardContent>
      </Card>

      {/* Body Measurements (Optional) */}
      <Card>
        <CardHeader>
          <CardTitle>Body Measurements (Optional)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormField
              type="number"
              label="Waist (cm)"
              value={data.measurements?.waist}
              onChange={(value) => updateMeasurement('waist', parseFloat(value) || '')}
              placeholder="80"
              step="0.5"
              min="40"
              max="200"
            />

            <FormField
              type="number"
              label="Chest (cm)"
              value={data.measurements?.chest}
              onChange={(value) => updateMeasurement('chest', parseFloat(value) || '')}
              placeholder="95"
              step="0.5"
              min="50"
              max="200"
            />

            <FormField
              type="number"
              label="Hips (cm)"
              value={data.measurements?.hips}
              onChange={(value) => updateMeasurement('hips', parseFloat(value) || '')}
              placeholder="90"
              step="0.5"
              min="50"
              max="200"
            />

            <FormField
              type="number"
              label="Neck (cm)"
              value={data.measurements?.neck}
              onChange={(value) => updateMeasurement('neck', parseFloat(value) || '')}
              placeholder="35"
              step="0.5"
              min="25"
              max="60"
            />

            <FormField
              type="number"
              label="Upper Arm (cm)"
              value={data.measurements?.upper_arm}
              onChange={(value) => updateMeasurement('upper_arm', parseFloat(value) || '')}
              placeholder="30"
              step="0.5"
              min="15"
              max="60"
            />

            <FormField
              type="number"
              label="Thigh (cm)"
              value={data.measurements?.thigh}
              onChange={(value) => updateMeasurement('thigh', parseFloat(value) || '')}
              placeholder="55"
              step="0.5"
              min="30"
              max="100"
            />
          </div>
          
          <div className="text-sm text-gray-500 bg-blue-50 p-3 rounded-lg">
            <strong>Tip:</strong> Body measurements help track progress beyond just weight. 
            Measure at the widest part of each area for consistency.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PhysicalMetricsStep;