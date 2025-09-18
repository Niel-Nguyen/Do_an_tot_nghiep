from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from models.data_models import ChatMessage, VietnameseDish
from models.ai_models import ai_models
from core.rag_system import rag_system
from utils.text_processor import text_processor
from config.settings import settings

class VietnameseFoodChatbot:
    """Chatbot tư vấn món ăn Việt Nam"""
    
    def __init__(self):
        self.conversation_history: List[ChatMessage] = []
        self.system_prompt = self._create_system_prompt()
        self.is_ready = False
    
    def initialize(self, dishes: List[VietnameseDish]) -> bool:
        """Khởi tạo chatbot với dữ liệu món ăn"""
        try:
            # Khởi tạo RAG system
            if not rag_system.initialize(dishes):
                return False
            
            self.is_ready = True
            print("Chatbot đã sẵn sàng!")
            return True
            
        except Exception as e:
            print(f"Lỗi khi khởi tạo chatbot: {e}")
            return False
    
    def chat(self, user_message: str) -> str:
        """Xử lý tin nhắn từ người dùng"""
        if not self.is_ready:
            return "Chatbot chưa được khởi tạo. Vui lòng kiểm tra lại."
        
        try:
            # Lưu tin nhắn người dùng
            self.conversation_history.append(
                ChatMessage(role="user", content=user_message)
            )
            
            # Tìm kiếm thông tin liên quan
            context = rag_system.get_context_for_llm(user_message)
            
            # Phân tích ý định câu hỏi
            intent = text_processor.analyze_query_intent(user_message)
            
            # Tạo prompt cho LLM
            full_prompt = self._create_full_prompt(user_message, context, intent)
            
            # Gọi LLM
            llm = ai_models.get_llm()
            response = llm.invoke(full_prompt)
            
            # Xử lý response
            bot_response = self._process_llm_response(response, intent)
            
            # Lưu phản hồi
            self.conversation_history.append(
                ChatMessage(role="assistant", content=bot_response)
            )
            
            return bot_response
            
        except Exception as e:
            error_msg = f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn: {str(e)}"
            self.conversation_history.append(
                ChatMessage(role="assistant", content=error_msg)
            )
            return error_msg
    
    def _create_system_prompt(self) -> str:
        """Tạo system prompt cho chatbot"""
        return """Bạn là một chuyên gia tư vấn món ăn Việt Nam thân thiện và hiểu biết sâu sắc. 

NHIỆM VỤ:
- Tư vấn món ăn Việt Nam dựa trên thông tin được cung cấp
- Đưa ra gợi ý phù hợp với nhu cầu và tình huống của người dùng
- Chia sẻ kiến thức về ẩm thực Việt Nam một cách sinh động và hấp dẫn

PHONG CÁCH TRÌNH BÀY:
- Thân thiện, nhiệt tình như một người bạn am hiểu ẩm thực
- Sử dụng tiếng Việt tự nhiên, dễ hiểu
- Tránh nói chuyện khô khan, hãy làm cho cuộc trò chuyện sinh động
- Đưa ra lời khuyên cụ thể và thực tế

QUY TẮC:
1. CHỈ tư vấn dựa trên thông tin món ăn được cung cấp trong CONTEXT
2. Nếu không có thông tin phù hợp, hãy thành thật nói và gợi ý hỏi khác
3. Luôn đề cập đến vùng miền của món ăn khi có thể
4. Nếu có link tham khảo, hãy đề xuất người dùng tham khảo thêm
5. Khuyến khích người dùng thử nghiệm và chia sẻ kinh nghiệm

ĐỊNH DẠNG PHẢN HỒI:
- Bắt đầu bằng lời chào thân thiện
- Trả lời trực tiếp câu hỏi
- Đưa ra thông tin chi tiết về món ăn (nguyên liệu, cách làm, đặc điểm)
- Kết thúc bằng câu hỏi hoặc gợi ý để duy trì cuộc trò chuyện

Hãy trả lời bằng tiếng Việt và giữ phong cách gần gụi, nhiệt tình!"""
    
    def _create_full_prompt(self, user_message: str, context: str, intent: Dict[str, Any]) -> List:
        """Tạo prompt đầy đủ cho LLM"""
        messages = [
            SystemMessage(content=self.system_prompt)
        ]
        
        # Thêm context từ RAG
        context_message = f"""
CONTEXT - Thông tin món ăn liên quan:
{context}

PHÂN TÍCH CÂU HỎI:
- Loại câu hỏi: {intent['type']}
- Từ khóa chính: {', '.join(intent['keywords'])}
- Bộ lọc: {str(intent['filters']) if intent['filters'] else 'Không có'}
"""
        
        messages.append(SystemMessage(content=context_message))
        
        # Thêm lịch sử hội thoại (giới hạn 5 tin nhắn gần nhất)
        recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        
        for msg in recent_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        
        # Thêm tin nhắn hiện tại
        messages.append(HumanMessage(content=user_message))
        
        return messages
    
    def _process_llm_response(self, response: Any, intent: Dict[str, Any]) -> str:
        """Xử lý phản hồi từ LLM"""
        try:
            # Lấy nội dung text từ response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Làm sạch và định dạng
            content = text_processor.clean_text(content)
            
            # Thêm emoji phù hợp dựa trên intent
            if intent['type'] == 'recipe':
                content = f"👨‍🍳 {content}"
            elif intent['type'] == 'ingredient':
                content = f"🛒 {content}"
            elif intent['type'] == 'recommendation':
                content = f"💡 {content}"
            elif intent['type'] == 'region':
                content = f"🗺️ {content}"
            else:
                content = f"🍜 {content}"
            
            return content
            
        except Exception as e:
            return f"Có lỗi khi xử lý phản hồi: {str(e)}"
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Lấy tóm tắt cuộc hội thoại"""
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len([msg for msg in self.conversation_history if msg.role == "user"]),
            'bot_messages': len([msg for msg in self.conversation_history if msg.role == "assistant"]),
            'recent_topics': self._extract_recent_topics()
        }
    
    def _extract_recent_topics(self) -> List[str]:
        """Trích xuất chủ đề gần đây"""
        topics = []
        recent_messages = self.conversation_history[-6:]  # 3 cặp hỏi-đáp gần nhất
        
        for msg in recent_messages:
            if msg.role == "user":
                keywords = text_processor.extract_keywords(msg.content)
                topics.extend(keywords[:2])  # Lấy 2 từ khóa chính
        
        # Loại bỏ trùng lặp và giữ tối đa 5 topics
        unique_topics = list(dict.fromkeys(topics))[:5]
        return unique_topics
    
    def clear_conversation(self):
        """Xóa lịch sử hội thoại"""
        self.conversation_history.clear()
    
    def get_suggested_questions(self) -> List[str]:
        """Gợi ý câu hỏi dựa trên ngữ cảnh"""
        base_questions = [
            "Bạn có thể gợi ý món ăn phù hợp với thời tiết hôm nay không?",
            "Tôi muốn tìm món ăn đặc sản miền Bắc",
            "Có món chay nào ngon và dễ làm không?",
            "Gợi ý món ăn phù hợp cho bữa tối gia đình",
            "Món nào phù hợp khi tôi đang buồn?",
            "Cách làm phở bò truyền thống như thế nào?",
            "Nguyên liệu cần thiết để làm bánh chưng là gì?",
            "Món ăn nào có thể làm nhanh trong 30 phút?",
        ]
        
        # Thêm câu hỏi dựa trên lịch sử (nếu có)
        recent_topics = self._extract_recent_topics()
        dynamic_questions = []
        
        for topic in recent_topics[:2]:
            dynamic_questions.append(f"Còn món nào khác liên quan đến {topic}?")
            dynamic_questions.append(f"Cách làm {topic} tại nhà như thế nào?")
        
        # Kết hợp và trộn ngẫu nhiên
        all_questions = base_questions + dynamic_questions
        return all_questions[:6]  # Trả về 6 gợi ý
    
    def get_chatbot_stats(self) -> Dict[str, Any]:
        """Thống kê về chatbot"""
        return {
            'is_ready': self.is_ready,
            'conversation_stats': self.get_conversation_summary(),
            'rag_stats': rag_system.get_statistics(),
            'system_info': {
                'model': settings.CHAT_MODEL,
                'provider': settings.MODEL_PROVIDER
            }
        }

# Global instance
vietnamese_food_chatbot = VietnameseFoodChatbot()