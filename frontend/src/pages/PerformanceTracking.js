import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AdminLayout from '@/components/AdminLayout';
import { Target, Star, Plus, User, Calendar, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PerformanceTracking = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [goals, setGoals] = useState([]);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('reviews');

  // Review form state
  const [reviewForm, setReviewForm] = useState({
    employee_number: '',
    review_period_start: '',
    review_period_end: '',
    overall_rating: 3,
    goals_achieved: '',
    strengths: '',
    areas_for_improvement: '',
    comments: ''
  });

  // Goal form state
  const [goalForm, setGoalForm] = useState({
    employee_number: '',
    goal_title: '',
    goal_description: '',
    target_date: '',
    priority: 'Medium'
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      fetchEmployeeData(selectedEmployee.employee_number);
    }
  }, [selectedEmployee]);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data.employees || response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load employees');
      setLoading(false);
    }
  };

  const fetchEmployeeData = async (employeeNumber) => {
    try {
      const [reviewsRes, goalsRes] = await Promise.all([
        axios.get(`${API}/performance/reviews/${employeeNumber}`),
        axios.get(`${API}/performance/goals/${employeeNumber}`)
      ]);
      setReviews(reviewsRes.data);
      setGoals(goalsRes.data);
    } catch (error) {
      console.error('Failed to fetch employee performance data');
    }
  };

  const handleCreateReview = async () => {
    if (!reviewForm.employee_number || !reviewForm.review_period_start || !reviewForm.review_period_end) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      await axios.post(`${API}/performance/reviews`, reviewForm);
      toast.success('Performance review created successfully');
      setShowReviewModal(false);
      setReviewForm({
        employee_number: '',
        review_period_start: '',
        review_period_end: '',
        overall_rating: 3,
        goals_achieved: '',
        strengths: '',
        areas_for_improvement: '',
        comments: ''
      });
      if (selectedEmployee) {
        fetchEmployeeData(selectedEmployee.employee_number);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create review');
    }
  };

  const handleCreateGoal = async () => {
    if (!goalForm.employee_number || !goalForm.goal_title || !goalForm.target_date) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      await axios.post(`${API}/performance/goals`, goalForm);
      toast.success('Goal created successfully');
      setShowGoalModal(false);
      setGoalForm({
        employee_number: '',
        goal_title: '',
        goal_description: '',
        target_date: '',
        priority: 'Medium'
      });
      if (selectedEmployee) {
        fetchEmployeeData(selectedEmployee.employee_number);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create goal');
    }
  };

  const openReviewModal = (employee = null) => {
    if (employee) {
      setReviewForm(prev => ({ ...prev, employee_number: employee.employee_number }));
    }
    setShowReviewModal(true);
  };

  const openGoalModal = (employee = null) => {
    if (employee) {
      setGoalForm(prev => ({ ...prev, employee_number: employee.employee_number }));
    }
    setShowGoalModal(true);
  };

  const renderStars = (rating, interactive = false, onChange = null) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => interactive && onChange && onChange(star)}
            className={`text-2xl ${interactive ? 'cursor-pointer' : 'cursor-default'} ${
              star <= rating ? 'text-yellow-500' : 'text-slate-300'
            }`}
            disabled={!interactive}
          >
            ★
          </button>
        ))}
      </div>
    );
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      'High': 'badge-danger',
      'Medium': 'badge-warning',
      'Low': 'badge-info'
    };
    return <span className={`badge ${colors[priority] || 'badge-info'}`}>{priority}</span>;
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="text-center py-12">Loading...</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div data-testid="performance-tracking-page">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Performance Tracking</h1>
            <p className="text-slate-600">Manage employee reviews and goals</p>
          </div>
          
          <div className="flex gap-3">
            <Button
              onClick={() => openReviewModal()}
              data-testid="create-review-btn"
              className="bg-blue-900 hover:bg-blue-800 text-white flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Review
            </Button>
            <Button
              onClick={() => openGoalModal()}
              data-testid="create-goal-btn"
              className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-2"
            >
              <Target className="w-4 h-4" />
              Set Goal
            </Button>
          </div>
        </div>

        {/* Employee Selection */}
        <div className="card p-6 mb-6">
          <label className="label">Select Employee</label>
          <Select 
            value={selectedEmployee?.employee_number || ''} 
            onValueChange={(value) => {
              const emp = employees.find(e => e.employee_number === value);
              setSelectedEmployee(emp);
            }}
          >
            <SelectTrigger data-testid="employee-select" className="w-full md:w-96">
              <SelectValue placeholder="Select an employee to view performance" />
            </SelectTrigger>
            <SelectContent>
              {employees.map((emp) => (
                <SelectItem key={emp.employee_number} value={emp.employee_number}>
                  {emp.first_name} {emp.last_name} ({emp.employee_number})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Employee Performance View */}
        {selectedEmployee ? (
          <div>
            {/* Employee Header */}
            <div className="card p-6 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="w-8 h-8 text-blue-900" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">
                    {selectedEmployee.first_name} {selectedEmployee.last_name}
                  </h2>
                  <p className="text-slate-600">{selectedEmployee.position} • {selectedEmployee.department}</p>
                  <p className="mono text-sm text-slate-500">{selectedEmployee.employee_number}</p>
                </div>
                <div className="ml-auto flex gap-3">
                  <Button
                    onClick={() => openReviewModal(selectedEmployee)}
                    data-testid="add-review-for-employee"
                    className="bg-blue-900 hover:bg-blue-800 text-white"
                  >
                    <Star className="w-4 h-4 mr-2" />
                    Add Review
                  </Button>
                  <Button
                    onClick={() => openGoalModal(selectedEmployee)}
                    data-testid="add-goal-for-employee"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  >
                    <Target className="w-4 h-4 mr-2" />
                    Set Goal
                  </Button>
                </div>
              </div>
            </div>

            {/* Tabs for Reviews and Goals */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                <TabsTrigger value="reviews" data-testid="reviews-tab">
                  <Star className="w-4 h-4 mr-2" />
                  Reviews ({reviews.length})
                </TabsTrigger>
                <TabsTrigger value="goals" data-testid="goals-tab">
                  <Target className="w-4 h-4 mr-2" />
                  Goals ({goals.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="reviews">
                <div className="space-y-4" data-testid="reviews-list">
                  {reviews.length === 0 ? (
                    <div className="card p-12 text-center text-slate-500">
                      No performance reviews yet
                    </div>
                  ) : (
                    reviews.map((review) => (
                      <div key={review.review_id} className="card p-6" data-testid={`review-${review.review_id}`}>
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <p className="label">Review Period</p>
                            <p className="mono text-lg">
                              {new Date(review.review_period_start).toLocaleDateString()} - {new Date(review.review_period_end).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="label">Overall Rating</p>
                            {renderStars(review.overall_rating)}
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="label">Goals Achieved</p>
                            <p className="text-slate-700">{review.goals_achieved || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="label">Strengths</p>
                            <p className="text-slate-700">{review.strengths || 'N/A'}</p>
                          </div>
                        </div>
                        
                        <div className="mb-4">
                          <p className="label">Areas for Improvement</p>
                          <p className="text-slate-700">{review.areas_for_improvement || 'N/A'}</p>
                        </div>
                        
                        {review.comments && (
                          <div className="mb-4">
                            <p className="label">Comments</p>
                            <p className="text-slate-700">{review.comments}</p>
                          </div>
                        )}
                        
                        <div className="text-sm text-slate-500 pt-4 border-t">
                          Reviewed by {review.reviewer_name} on {new Date(review.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>

              <TabsContent value="goals">
                <div className="space-y-4" data-testid="goals-list">
                  {goals.length === 0 ? (
                    <div className="card p-12 text-center text-slate-500">
                      No goals set yet
                    </div>
                  ) : (
                    goals.map((goal) => (
                      <div key={goal.goal_id} className="card p-6" data-testid={`goal-${goal.goal_id}`}>
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <h3 className="text-lg font-semibold text-slate-900">{goal.goal_title}</h3>
                            <p className="text-slate-600 mt-1">{goal.goal_description}</p>
                          </div>
                          <div className="text-right">
                            {getPriorityBadge(goal.priority)}
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-6 text-sm">
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-slate-500" />
                            <span className="text-slate-600">Target: {new Date(goal.target_date).toLocaleDateString()}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`badge ${goal.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                              {goal.status === 'in_progress' ? 'In Progress' : goal.status}
                            </span>
                          </div>
                        </div>
                        
                        <div className="text-sm text-slate-500 pt-4 border-t mt-4">
                          Set by {goal.set_by} on {new Date(goal.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        ) : (
          <div className="card p-12 text-center">
            <TrendingUp className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">Select an Employee</h3>
            <p className="text-slate-500">Choose an employee from the dropdown to view their performance data</p>
          </div>
        )}

        {/* Create Review Modal */}
        <Dialog open={showReviewModal} onOpenChange={setShowReviewModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Create Performance Review</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <label className="label">Employee *</label>
                <Select 
                  value={reviewForm.employee_number} 
                  onValueChange={(value) => setReviewForm(prev => ({ ...prev, employee_number: value }))}
                >
                  <SelectTrigger data-testid="review-employee-select">
                    <SelectValue placeholder="Select employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((emp) => (
                      <SelectItem key={emp.employee_number} value={emp.employee_number}>
                        {emp.first_name} {emp.last_name} ({emp.employee_number})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Review Period Start *</label>
                  <input
                    type="date"
                    data-testid="review-period-start"
                    className="input-field"
                    value={reviewForm.review_period_start}
                    onChange={(e) => setReviewForm(prev => ({ ...prev, review_period_start: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="label">Review Period End *</label>
                  <input
                    type="date"
                    data-testid="review-period-end"
                    className="input-field"
                    value={reviewForm.review_period_end}
                    onChange={(e) => setReviewForm(prev => ({ ...prev, review_period_end: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="label">Overall Rating *</label>
                {renderStars(reviewForm.overall_rating, true, (rating) => setReviewForm(prev => ({ ...prev, overall_rating: rating })))}
              </div>

              <div>
                <label className="label">Goals Achieved</label>
                <textarea
                  data-testid="goals-achieved-input"
                  className="input-field"
                  rows="2"
                  value={reviewForm.goals_achieved}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, goals_achieved: e.target.value }))}
                  placeholder="Describe goals achieved during this period"
                />
              </div>

              <div>
                <label className="label">Strengths</label>
                <textarea
                  data-testid="strengths-input"
                  className="input-field"
                  rows="2"
                  value={reviewForm.strengths}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, strengths: e.target.value }))}
                  placeholder="List key strengths"
                />
              </div>

              <div>
                <label className="label">Areas for Improvement</label>
                <textarea
                  data-testid="areas-improvement-input"
                  className="input-field"
                  rows="2"
                  value={reviewForm.areas_for_improvement}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, areas_for_improvement: e.target.value }))}
                  placeholder="Suggest areas for growth"
                />
              </div>

              <div>
                <label className="label">Additional Comments</label>
                <textarea
                  data-testid="review-comments-input"
                  className="input-field"
                  rows="2"
                  value={reviewForm.comments}
                  onChange={(e) => setReviewForm(prev => ({ ...prev, comments: e.target.value }))}
                  placeholder="Any additional feedback"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleCreateReview}
                  data-testid="submit-review-btn"
                  className="bg-blue-900 hover:bg-blue-800 text-white flex-1"
                >
                  Create Review
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowReviewModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Create Goal Modal */}
        <Dialog open={showGoalModal} onOpenChange={setShowGoalModal}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold">Set Performance Goal</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <label className="label">Employee *</label>
                <Select 
                  value={goalForm.employee_number} 
                  onValueChange={(value) => setGoalForm(prev => ({ ...prev, employee_number: value }))}
                >
                  <SelectTrigger data-testid="goal-employee-select">
                    <SelectValue placeholder="Select employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((emp) => (
                      <SelectItem key={emp.employee_number} value={emp.employee_number}>
                        {emp.first_name} {emp.last_name} ({emp.employee_number})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="label">Goal Title *</label>
                <input
                  type="text"
                  data-testid="goal-title-input"
                  className="input-field"
                  value={goalForm.goal_title}
                  onChange={(e) => setGoalForm(prev => ({ ...prev, goal_title: e.target.value }))}
                  placeholder="e.g., Complete project management certification"
                />
              </div>

              <div>
                <label className="label">Description</label>
                <textarea
                  data-testid="goal-description-input"
                  className="input-field"
                  rows="3"
                  value={goalForm.goal_description}
                  onChange={(e) => setGoalForm(prev => ({ ...prev, goal_description: e.target.value }))}
                  placeholder="Detailed description of the goal"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Target Date *</label>
                  <input
                    type="date"
                    data-testid="goal-target-date"
                    className="input-field"
                    value={goalForm.target_date}
                    onChange={(e) => setGoalForm(prev => ({ ...prev, target_date: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="label">Priority</label>
                  <Select 
                    value={goalForm.priority} 
                    onValueChange={(value) => setGoalForm(prev => ({ ...prev, priority: value }))}
                  >
                    <SelectTrigger data-testid="goal-priority-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="High">High</SelectItem>
                      <SelectItem value="Medium">Medium</SelectItem>
                      <SelectItem value="Low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleCreateGoal}
                  data-testid="submit-goal-btn"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white flex-1"
                >
                  Create Goal
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowGoalModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
};

export default PerformanceTracking;
