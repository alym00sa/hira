// Mock meeting data for demo/screenshots
export const mockMeetings = [
  {
    id: "meeting-001",
    title: "AI Policy Strategy Workshop",
    date: "2024-11-28T14:00:00Z",
    duration: "45 min",
    participants: [
      { name: "Sarah Chen", email: "sarah.chen@example.com" },
      { name: "Marcus Johnson", email: "marcus.j@example.com" },
      { name: "Dr. Amelia Torres", email: "a.torres@example.com" },
      { name: "James Park", email: "jpark@example.com" }
    ],
    summary: "Comprehensive discussion on developing AI governance frameworks aligned with human rights principles. Team reviewed current EU AI Act compliance requirements and mapped out implementation strategy for Q1 2025. Emphasis placed on transparency, accountability, and stakeholder engagement throughout the policy development process.",
    key_topics: [
      "EU AI Act Compliance",
      "Human Rights Framework",
      "Transparency Requirements",
      "Stakeholder Engagement",
      "Risk Assessment Protocols"
    ],
    action_items: [
      {
        task: "Draft AI governance framework document incorporating HRBA principles",
        assignee: "Sarah Chen",
        due_date: "2024-12-15",
        status: "in_progress"
      },
      {
        task: "Schedule stakeholder consultation sessions with civil society groups",
        assignee: "Marcus Johnson",
        due_date: "2024-12-10",
        status: "completed"
      },
      {
        task: "Conduct risk assessment for high-risk AI systems",
        assignee: "Dr. Amelia Torres",
        due_date: "2024-12-20",
        status: "pending"
      }
    ],
    transcript: `Sarah Chen: Good afternoon everyone. Let's dive into our AI policy strategy discussion. As you know, the EU AI Act is now in force, and we need to ensure our frameworks are compliant while maintaining our commitment to human rights-based approaches.

Marcus Johnson: Absolutely. I've been reviewing the transparency requirements, and they align well with our existing principles. The key challenge will be operationalizing them across all our AI systems.

Dr. Amelia Torres: I agree. From a technical standpoint, we need to think about how we document our algorithms, data sources, and decision-making processes. The risk assessment framework is particularly important for our high-risk applications.

James Park: Should we be looking at the OECD AI principles as well? They provide good guidance on trustworthy AI that complements the EU Act.

Sarah Chen: Great point, James. Let's make sure we're incorporating best practices from multiple frameworks. Marcus, can you lead the stakeholder engagement process? We need input from civil society organizations.

Marcus Johnson: Definitely. I'll set up consultation sessions for next week. We should include representatives from digital rights groups and affected communities.

Dr. Amelia Torres: I'll work on the risk assessment protocols. We need to categorize our systems and identify which ones fall under high-risk categories.

Sarah Chen: Perfect. Let's aim to have a draft framework by mid-December. This needs to be thorough but also practical for implementation.`
  },
  {
    id: "meeting-002",
    title: "AI Wearables: Privacy and Ethics Discussion",
    date: "2024-11-25T10:30:00Z",
    duration: "52 min",
    participants: [
      { name: "Dr. Lisa Rodriguez", email: "l.rodriguez@example.com" },
      { name: "Kevin Tanaka", email: "ktanaka@example.com" },
      { name: "Priya Sharma", email: "priya.s@example.com" },
      { name: "Alex Morrison", email: "a.morrison@example.com" }
    ],
    summary: "In-depth exploration of privacy implications and ethical considerations for AI-powered wearable devices. Discussion covered data collection practices, user consent mechanisms, and the balance between personalization and privacy. Team identified need for enhanced transparency in data usage and stronger opt-out options for sensitive health data processing.",
    key_topics: [
      "Privacy by Design",
      "Health Data Protection",
      "User Consent Mechanisms",
      "Continuous Monitoring Ethics",
      "Data Minimization Strategies"
    ],
    action_items: [
      {
        task: "Design new consent flow for wearable app with granular permissions",
        assignee: "Priya Sharma",
        due_date: "2024-12-08",
        status: "in_progress"
      },
      {
        task: "Conduct privacy impact assessment for health monitoring features",
        assignee: "Dr. Lisa Rodriguez",
        due_date: "2024-12-12",
        status: "pending"
      },
      {
        task: "Review third-party data sharing agreements and update policies",
        assignee: "Alex Morrison",
        due_date: "2024-12-15",
        status: "pending"
      }
    ],
    transcript: `Dr. Lisa Rodriguez: Thanks for joining today's session on AI wearables. This is a critical area where technology meets very personal health data. We need to get this right from both a privacy and ethics perspective.

Kevin Tanaka: I've been researching GDPR compliance for wearables. The continuous data collection aspect raises interesting questions about ongoing consent. Users often forget what they've agreed to.

Priya Sharma: That's a huge UX challenge. How do we keep users informed without overwhelming them with notifications? We need transparency that's actually usable.

Alex Morrison: From a legal standpoint, we're seeing increasing scrutiny on health data. The combination of AI-driven insights and continuous monitoring creates new risks we haven't dealt with before.

Dr. Lisa Rodriguez: Let's talk about data minimization. Are we collecting more than we need? Kevin, what's your take on the technical side?

Kevin Tanaka: We could definitely reduce the frequency of certain data points. Not everything needs to be collected continuously. We should only gather what's necessary for the specific features users have enabled.

Priya Sharma: I think we need a major overhaul of our consent flow. Users should be able to choose exactly what types of data they're comfortable sharing, with clear explanations of what each permission enables.

Alex Morrison: Agreed. And we need stronger opt-out mechanisms, especially for the more sensitive health predictions. Users should always be in control.

Dr. Lisa Rodriguez: Great discussion. Let's move forward with these privacy-first principles and reconvene once we have concrete proposals.`
  },
  {
    id: "meeting-003",
    title: "Strategic Partnerships for AI Development",
    date: "2024-11-20T15:00:00Z",
    duration: "38 min",
    participants: [
      { name: "Rachel Kim", email: "rachel.kim@example.com" },
      { name: "David Chen", email: "d.chen@example.com" },
      { name: "Dr. Samuel Okonkwo", email: "s.okonkwo@example.com" }
    ],
    summary: "Strategic planning session focused on identifying and establishing partnerships with organizations committed to responsible AI development. Discussions covered potential collaborations with academic institutions, civil society organizations, and private sector partners. Team agreed on criteria for partner selection emphasizing alignment with human rights values and commitment to ethical AI practices.",
    key_topics: [
      "Academic Collaborations",
      "Civil Society Partnerships",
      "Open Source Initiatives",
      "Research Funding Opportunities",
      "Knowledge Sharing Programs"
    ],
    action_items: [
      {
        task: "Reach out to three universities for research partnerships on responsible AI",
        assignee: "Dr. Samuel Okonkwo",
        due_date: "2024-12-05",
        status: "completed"
      },
      {
        task: "Draft partnership criteria document and approval workflow",
        assignee: "Rachel Kim",
        due_date: "2024-12-10",
        status: "in_progress"
      },
      {
        task: "Identify funding opportunities for joint research initiatives",
        assignee: "David Chen",
        due_date: "2024-12-18",
        status: "pending"
      }
    ],
    transcript: `Rachel Kim: Good afternoon. Let's discuss our partnership strategy for responsible AI development. We've identified this as a key priority for expanding our impact.

David Chen: I think we should focus on three areas: academic institutions for research, civil society for community input, and select private sector partners who share our values.

Dr. Samuel Okonkwo: From an academic perspective, there's strong interest in collaborative research on AI ethics and human rights. I've had preliminary conversations with several universities.

Rachel Kim: That's excellent. What kind of partnerships are they interested in?

Dr. Samuel Okonkwo: Mostly joint research projects, PhD student collaborations, and access to our real-world implementation data for academic studies. There's also interest in co-developing educational programs.

David Chen: On the funding side, I've been looking into grants from foundations focused on AI and human rights. There are some promising opportunities that require consortium applications.

Rachel Kim: Perfect. We should definitely pursue those. What about civil society partnerships?

David Chen: I think we need partners who can provide ground-level insights into how AI impacts communities. Organizations working on digital rights, economic justice, and marginalized communities.

Dr. Samuel Okonkwo: Agreed. They bring perspectives we might miss from our technical focus. It keeps us accountable too.

Rachel Kim: Let's develop clear criteria for selecting partners and a structured process for establishing these relationships. Samuel, can you take the lead on academic outreach?

Dr. Samuel Okonkwo: Absolutely. I'll have some concrete proposals by early December.`
  },
  {
    id: "meeting-004",
    title: "Building AI Agents for Healthcare Applications",
    date: "2024-11-15T13:00:00Z",
    duration: "61 min",
    participants: [
      { name: "Dr. Maria Santos", email: "m.santos@example.com" },
      { name: "Robert Chen", email: "rchen@example.com" },
      { name: "Nina Patel", email: "nina.p@example.com" },
      { name: "Dr. James Mitchell", email: "j.mitchell@example.com" },
      { name: "Sophie Laurent", email: "s.laurent@example.com" }
    ],
    summary: "Comprehensive technical discussion on developing AI agents for healthcare settings with emphasis on patient safety, clinical validation, and regulatory compliance. Team reviewed use cases including diagnostic support, patient triage, and care coordination. Strong focus placed on explainability requirements, clinical validation protocols, and ensuring healthcare providers maintain ultimate decision-making authority.",
    key_topics: [
      "Clinical Validation Requirements",
      "Patient Safety Protocols",
      "Explainable AI for Healthcare",
      "Regulatory Compliance (FDA, MDR)",
      "Healthcare Provider Oversight",
      "Bias Detection in Medical AI"
    ],
    action_items: [
      {
        task: "Develop explainability framework for diagnostic support AI agent",
        assignee: "Robert Chen",
        due_date: "2024-12-20",
        status: "in_progress"
      },
      {
        task: "Create clinical validation protocol with hospital partner",
        assignee: "Dr. Maria Santos",
        due_date: "2024-12-15",
        status: "in_progress"
      },
      {
        task: "Research FDA regulatory pathways for AI medical devices",
        assignee: "Nina Patel",
        due_date: "2024-12-10",
        status: "completed"
      },
      {
        task: "Design bias testing framework for patient triage system",
        assignee: "Sophie Laurent",
        due_date: "2024-12-22",
        status: "pending"
      }
    ],
    transcript: `Dr. Maria Santos: Welcome everyone. Today we're tackling a critical topic - AI agents in healthcare. This is high-stakes territory where mistakes can have serious consequences.

Robert Chen: Absolutely. I've been working on our diagnostic support agent, and the explainability requirements are intense. Clinicians need to understand why the AI is making specific recommendations.

Dr. James Mitchell: From a medical perspective, that's non-negotiable. Healthcare providers need to be able to interrogate the AI's reasoning and maintain final decision authority. We can't have black box systems making clinical decisions.

Nina Patel: On the regulatory side, FDA has clear guidance on AI as a medical device. We need to think about our intended use claims very carefully. Are we providing decision support or making autonomous decisions?

Dr. Maria Santos: Decision support only. The clinician always makes the final call. What about bias detection? We know AI can perpetuate healthcare disparities.

Sophie Laurent: I'm developing a comprehensive testing framework for that. We need to evaluate performance across different demographic groups, check for socioeconomic biases, and monitor for disparate impacts.

Robert Chen: How do we balance accuracy with explainability? Sometimes the most accurate models are the least interpretable.

Dr. James Mitchell: In healthcare, explainability often trumps a few percentage points of accuracy. Clinicians won't trust systems they don't understand, and they shouldn't.

Nina Patel: We also need robust clinical validation. Not just technical metrics, but real-world clinical outcomes with actual patients and providers.

Dr. Maria Santos: Agreed. Let's partner with a hospital for a pilot study. We need their clinical expertise throughout the development process, not just at the end.

Sophie Laurent: And we need continuous monitoring post-deployment. Healthcare AI isn't "set it and forget it." Populations change, medical practices evolve.

Dr. Maria Santos: Excellent points all around. This is going to be a long development cycle, but patient safety demands we get it right. Let's move forward methodically.`
  },
  {
    id: "meeting-005",
    title: "AI Agents for Education: Equity and Access",
    date: "2024-11-10T11:00:00Z",
    duration: "47 min",
    participants: [
      { name: "Dr. Aisha Mohammed", email: "a.mohammed@example.com" },
      { name: "Carlos Mendez", email: "cmendez@example.com" },
      { name: "Jennifer Wu", email: "jennifer.wu@example.com" },
      { name: "Prof. Michael Brown", email: "m.brown@example.com" }
    ],
    summary: "Strategic session on developing AI educational agents that promote equity and expand access to quality learning resources. Discussion emphasized need for culturally responsive AI, multilingual support, and adaptation to diverse learning styles. Team identified digital divide as critical challenge and committed to ensuring solutions work in low-connectivity environments.",
    key_topics: [
      "Educational Equity",
      "Digital Divide Solutions",
      "Culturally Responsive AI",
      "Multilingual Support",
      "Adaptive Learning Paths",
      "Teacher Empowerment"
    ],
    action_items: [
      {
        task: "Research low-bandwidth educational AI solutions for rural areas",
        assignee: "Carlos Mendez",
        due_date: "2024-12-12",
        status: "in_progress"
      },
      {
        task: "Develop culturally adaptive content framework for educational AI",
        assignee: "Dr. Aisha Mohammed",
        due_date: "2024-12-18",
        status: "pending"
      },
      {
        task: "Design teacher dashboard for AI agent oversight and customization",
        assignee: "Jennifer Wu",
        due_date: "2024-12-15",
        status: "in_progress"
      },
      {
        task: "Pilot multilingual support with three target languages",
        assignee: "Prof. Michael Brown",
        due_date: "2024-12-20",
        status: "pending"
      }
    ],
    transcript: `Dr. Aisha Mohammed: Good morning everyone. Today's focus is on AI agents for education, specifically how we ensure they promote equity rather than exacerbate existing inequalities.

Carlos Mendez: That's the trillion dollar question. Right now, most educational AI benefits students who already have advantages - good internet, devices, digital literacy. We need to flip that.

Jennifer Wu: I've been thinking about the teacher's role. AI shouldn't replace teachers but empower them. Teachers know their students' needs better than any algorithm.

Prof. Michael Brown: Absolutely. And we need cultural responsiveness. An AI tutor trained primarily on Western educational content won't serve students in different cultural contexts well.

Dr. Aisha Mohammed: Language is another huge barrier. Can we support multiple languages effectively? Not just translation, but culturally appropriate educational content in those languages.

Carlos Mendez: On the technical side, we need solutions that work in low-connectivity environments. Many schools, especially in rural areas, don't have reliable internet.

Jennifer Wu: What about offline-capable AI? Models that can run locally on basic devices?

Carlos Mendez: That's challenging but feasible. We'd need to optimize models heavily, but it's possible. We can sync with cloud when connectivity is available for updates.

Prof. Michael Brown: The adaptive learning piece is critical too. Students learn at different paces and in different ways. Our AI needs to recognize and adapt to that diversity.

Dr. Aisha Mohammed: And we must be careful about data collection and privacy, especially with children. What data do we actually need versus what's nice to have?

Jennifer Wu: Let's design the teacher dashboard with strong oversight capabilities. Teachers should see what the AI is teaching, how students are engaging, and be able to intervene or redirect.

Prof. Michael Brown: We should pilot this in diverse settings - urban and rural, different countries, different resource levels. That's how we'll learn what actually works for equity.

Dr. Aisha Mohammed: Agreed. Let's move forward with pilots that explicitly test our equity goals. If the AI doesn't reduce inequalities, we need to know that early and adjust.`
  }
];

export default mockMeetings;
