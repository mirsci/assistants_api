## Design abstractions over the inference engines

Abstractions for inference engines, SLMs so they can be easily replaced

**Benefits**
* Easy to switch engines (great for benchmarking on Mac Catalyst vs iPhone).
* Clean separation of concerns.
* Works inside the strict sandbox

```swift
import Foundation

// MARK: - Core Protocol (Improved)
@MainActor
protocol LLMInferenceEngine: AnyObject, Observable {
    var isInitialized: Bool { get }
    var isGenerating: Bool { get }
    var lastOutput: String { get }
    var errorMessage: String? { get }
    
    func initialize(modelURL: URL, options: EngineOptions?) async throws
    func sendPrompt(_ prompt: String, parameters: InferenceParameters) async throws -> String
    func sendPromptStreaming(_ prompt: String, parameters: InferenceParameters, onToken: @escaping (String) -> Void) async throws
    func runReasoningTest() async throws -> String
    func resetConversation() async
}

// Configuration options
struct EngineOptions {
    var contextLength: Int = 32768
    var maxTokens: Int = 2048
    var gpuLayers: Int? = nil          // llama.cpp / Cactus specific
    var backend: BackendPreference = .auto
}

enum BackendPreference {
    case auto
    case gpu
    case cpu
    case neuralEngine   // LiteRT / Apple-specific
}

struct InferenceParameters {
    var temperature: Float = 0.7
    var topP: Float = 0.9
    var maxTokens: Int = 2048
}
```

**Cactus engine implementation**

```swift
// Requires: https://github.com/mhayes853/swift-cactus or Kotlin Multiplatform bindings
import Cactus  // Swift SDK module

@MainActor
final class CactusEngine: LLMInferenceEngine {
    private var session: CactusSession?
    
    private(set) var isInitialized = false
    private(set) var isGenerating = false
    private(set) var lastOutput = ""
    private(set) var errorMessage: String?
    
    func initialize(modelURL: URL, options: EngineOptions? = nil) async throws {
        let opts = options ?? EngineOptions()
        
        let config = CactusConfig(
            modelPath: modelURL.path,
            contextLength: opts.contextLength,
            gpuLayers: opts.gpuLayers ?? 999,   // Aggressive offload on Apple Silicon
            cacheDir: NSTemporaryDirectory()    // Sandbox-safe
        )
        
        session = try await CactusSession(config: config)
        isInitialized = true
        print("✅ Cactus Engine initialized with Gemma 4")
    }
    
    func sendPrompt(_ prompt: String, parameters: InferenceParameters) async throws -> String {
        guard let session = session else { throw NSError(domain: "Cactus", code: -1) }
        
        isGenerating = true
        defer { isGenerating = false }
        
        let result = try await session.complete(
            prompt: prompt,
            temperature: parameters.temperature,
            topP: parameters.topP,
            maxTokens: parameters.maxTokens
        )
        
        lastOutput = result.text
        return result.text
    }
    
    func sendPromptStreaming(_ prompt: String, parameters: InferenceParameters, onToken: @escaping (String) -> Void) async throws {
        guard let session = session else { throw NSError(...) }
        
        isGenerating = true
        defer { isGenerating = false }
        
        try await session.completeStreaming(
            prompt: prompt,
            temperature: parameters.temperature,
            onToken: { token in
                DispatchQueue.main.async {
                    onToken(token)
                }
            }
        )
    }
    
    func runReasoningTest() async throws -> String {
        let prompt = """
        You are a world-class reasoning engine. Think step by step and be concise.
        
        Problem: A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?
        """
        return try await sendPrompt(prompt, parameters: InferenceParameters(temperature: 0.0))
    }
    
    func resetConversation() async {
        // Cactus sessions can be reset or recreated
        session?.resetContext()
    }
}
```

**LLM Service** 

```swift
enum InferenceEngineType: String, CaseIterable, Identifiable {
    case liteRT = "LiteRT-LM"
    case llamaCpp = "llama.cpp"
    case cactus = "Cactus"
    
    var id: String { rawValue }
    var title: String { rawValue }
}

@MainActor
final class LLMService: ObservableObject {
    @Published var currentEngine: LLMInferenceEngine
    @Published var engineType: InferenceEngineType
    
    init(preferred: InferenceEngineType = .cactus) {   // Default to Cactus for mobile perf
        self.engineType = preferred
        self.currentEngine = Self.createEngine(preferred)
    }
    
    private static func createEngine(_ type: InferenceEngineType) -> LLMInferenceEngine {
        switch type {
        case .liteRT:    return LiteRTLMEngine()
        case .llamaCpp:  return LlamaCppEngine()
        case .cactus:    return CactusEngine()
        }
    }
    
    func switchEngine(to type: InferenceEngineType) {
        engineType = type
        currentEngine = Self.createEngine(type)
    }
    
    func initializeWithGemma4(options: EngineOptions? = nil) async throws {
        let modelURL = ModelManager.shared.gemma4E4BURL
        try await currentEngine.initialize(modelURL: modelURL, options: options)
    }
}
```

## Session manager
Session manager for multiple sessions/conversations and multiturn conversations and long conversations
Conversation manager for monitoring the memory pressure

```swift
@MainActor
protocol ConversationSession: AnyObject, Observable {
    var sessionId: String { get }
    var messages: [ChatMessage] { get }
    
    func sendMessage(_ content: String, parameters: InferenceParameters) async throws -> String
    func sendMessageStreaming(_ content: String, parameters: InferenceParameters) -> AsyncThrowingStream<String, Error>
    
    func addSystemMessage(_ content: String)
    func clearHistory()
    func save() async throws -> Data   // For persistence
}

@MainActor
final class LLMService {
    private var activeSessions: [String: ConversationSession] = [:]
    
    func createSession(sessionId: String = UUID().uuidString, systemPrompt: String? = nil) -> ConversationSession {
        let session = makeSession(for: currentEngineType, sessionId: sessionId)
        if let systemPrompt {
            session.addSystemMessage(systemPrompt)
        }
        activeSessions[sessionId] = session
        return session
    }
    
    func getSession(id: String) -> ConversationSession? {
        activeSessions[id]
    }
}

class ConversationManager {
    func createSession(...) async -> ConversationSession {
        let session = ...
        // Monitor total memory usage across all sessions
        Task { await monitorMemoryPressure() }
        return session
    }
}
```
