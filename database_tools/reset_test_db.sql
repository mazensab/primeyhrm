-- 🧭 ملف: reset_test_db.sql
-- 🧱 الوظيفة: حذف قاعدة بيانات الاختبار وإعادة إنشائها بإعدادات الترميز الصحيحة (MariaDB 10.x)
-- ⚙️ مخصص لمشروع: Mham Cloud

-- ⚠️ تأكد من أنك تستخدم مستخدم يملك صلاحية DROP/CREATE (مثل root)
-- يمكنك تنفيذ الملف بالأمر التالي من PowerShell:
-- mysql -u root -p < C:\Users\mazen\primeyhrm\database_tools\reset_test_db.sql

-- 🧹 حذف قاعدة الاختبار إن وُجدت
DROP DATABASE IF EXISTS test_primey_hrm;

-- 🏗️ إعادة إنشاء القاعدة بنفس الترميز المستخدم في المشروع
CREATE DATABASE test_primey_hrm
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- ✅ التأكيد
USE test_primey_hrm;

-- 🧾 ملاحظة:
-- لا حاجة لإنشاء الجداول يدويًا، Django سيتكفل بذلك عند تشغيل الاختبارات:
-- python manage.py test notification_center;

SELECT "✅ تم إعادة إنشاء قاعدة بيانات الاختبار بنجاح." AS status;
