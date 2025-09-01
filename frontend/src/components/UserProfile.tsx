import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Button, Input, Card } from "./ui";
import { apiService } from "../services/api";

interface UserProfileData {
  full_name?: string;
  bio?: string;
  website?: string;
  location?: string;
  timezone?: string;
}

export const UserProfile: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const [profile, setProfile] = useState<UserProfileData>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const response = await apiService.get("/auth/me");
      if (response.data) {
        setProfile({
          full_name: response.data.full_name || "",
          bio: response.data.bio || "",
          website: response.data.website || "",
          location: response.data.location || "",
          timezone: response.data.timezone || "",
        });
      }
    } catch (err) {
      console.error("Error loading profile:", err);
      setError("Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await apiService.put("/auth/profile", profile);

      if (response.data) {
        setSuccess("Profile updated successfully");
        // Update the profile in context if needed
        if (profile.full_name) {
          await updateProfile({ displayName: profile.full_name });
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof UserProfileData, value: string) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">User Profile</h1>
        <p className="text-gray-600">
          Manage your account information and preferences
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-md">
              {success}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Full Name"
              value={profile.full_name || ""}
              onChange={(value) => handleInputChange("full_name", value)}
              placeholder="Enter your full name"
            />

            <Input
              label="Email"
              value={user?.email || ""}
              disabled
              placeholder="Email address"
            />
          </div>

          <Input
            label="Bio"
            value={profile.bio || ""}
            onChange={(value) => handleInputChange("bio", value)}
            placeholder="Tell us about yourself"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Website"
              value={profile.website || ""}
              onChange={(value) => handleInputChange("website", value)}
              placeholder="https://your-website.com"
            />

            <Input
              label="Location"
              value={profile.location || ""}
              onChange={(value) => handleInputChange("location", value)}
              placeholder="City, Country"
            />
          </div>

          <Input
            label="Timezone"
            value={profile.timezone || ""}
            onChange={(value) => handleInputChange("timezone", value)}
            placeholder="e.g., UTC, America/New_York"
          />

          <div className="flex justify-end space-x-4">
            <Button
              type="button"
              variant="secondary"
              onClick={loadProfile}
              disabled={saving}
            >
              Reset
            </Button>
            <Button type="submit" loading={saving} disabled={saving}>
              Save Changes
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
